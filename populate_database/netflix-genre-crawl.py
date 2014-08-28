#!/usr/bin/env python
# TODO make range command line arguments

import sys, codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout) # if your terminal can't do utf-8, well...

import time
import urllib2

import sqlite3

from optparse import OptionParser

import BeautifulSoup

cookie = """NetflixId=v%3D2%26mac%3DAQEAEAABABSXl5BfGDOFFiwdC4Jj4HaL2MdlvhPtc6Y.%26ch%3DAQEAEAABABQ3ipAjBCfQcyKybFUhPJK3euvsGkOzkXM.%26ct%3DBQAOAAEBEL_oxQE_wTOcVj81qwvAOmmCMBDxKoyjtJ88PvEER9Giu90TVFjRx_AuoZuffesCFBO4_NIpEsXxBt_tk-4_5C1jWW9wB8bZcfwdD8HilK7XU-WIEjGlSrAfW2sISfLEPM_lFuXslPtRONm97bLOEYUVx7ac9SIqS4zGFOxTGY-3iGiWVWqgUzcsQFlbKkH-FoYCLCb2LjVIRsC55S2dxAXP57AyWlw_q8635IRKApCYfpUhufaiAAHyzW7QdgRNWoliTnsDCHnTBv8D5IFvExZEoBOJQ1_JwwYeVoLN09_mHZcmE6_jDeHpYqy9zopcEDedDhKooJiEoCSMSw4g2wSlB95j6llj5YzYUe3DJE5_iqaFPiVJbO0yZjgjzpDG8r98CgOAy93ZRJ3gbAFa3uMJnxnfMg118zMA3C5wU3FnClj1E_u7TpcioOOrhjNIgH0NfvlIGRNvc3Yw6nlSRPXejBoUoXXX1_unaBbQHPcRnDPOClC-WKSR3pGLrXXtCL0ngUtKVL_uXCxhnIkoYgRc7SZZtUoOiOmB5745qJsnregKfomQ7nSE8-GzjnAfSNtlwqJfl7YLKIDof2TW3u2QJtZikrRbLd6Km7A_lHa8C41TDijunCwurZFBsssZToPHpMeJQRrK7c5um-xwIRzkIugn9Vi97OMBAEcgnxG4z70NC9Cm2xV461b5-jP23Am-UaRkhYHZgv44cI_t4NIX6vuQ1_Ep4nBhwAwqaYBGgCYGP2e0UMo5o_-62wLHDmL0%26bt%3Dusr;profilesNewSession=0;profilesNewUser=0"""

def get_genre(i, extra):
    opener = urllib2.build_opener()
    opener.addheaders.append(('Cookie', cookie))

    url = "http://movies.netflix.com/WiAltGenre?agid=%s" % i
    try:
        page = opener.open(url)
    except urllib2.HTTPError:
        print "%s [skipped]" % i
        c.execute('INSERT INTO genres (genre_id, url, skipped) VALUES (?,?,?)', (i, url, True))
        return

    # new_cookie = page.info().getheader('Set-Cookie')

    soup = BeautifulSoup.BeautifulSoup(page.read())

    name = soup.find('div', {'class': 'crumb'})
    genre = name.getText().strip()
    # TODO if "Subgenre" in genre: ...

    if not extra:
        if name:
            c.execute('INSERT INTO genres (genre_id, name, url) VALUES (?,?,?)', (i, genre, url))
        # print "%s (%s)" % (genre, i)

    if extra:
        movie_data = []

        gallery = soup.find('div', {'class': 'agMovieSet agMovieGallery'})
        if gallery:
            for movie in gallery.contents:
                cover_img = movie.find('img')
                cover_url = cover_img['src']
                name = cover_img['alt']

                cover_link = movie.find('a')
                play_url = cover_link['href']
                ui_track = cover_link['data-uitrack']
            
                movie_data.append((name, cover_url, play_url, ui_track, i))

            # print "%s (%s)" % (genre, i)
            # for movie in movie_data:
            #     print "\t%s (%s)" % (movie[0], movie[3])

            c.execute('INSERT INTO genres (genre_id, name, url, movie_count) VALUES (?,?,?,?)', (i, genre, url, len(movie_data)))
            c.executemany('INSERT INTO movies (name, cover_url, movie_url, info, genres) VALUES (?,?,?,?,?)', movie_data)

        else:
            if name:
                c.execute('INSERT INTO genres (genre_id, name, url, movie_count) VALUES (?,?,?,?)', (i, genre, url, 0))
            else:
                # print "No genre name found for ID %s" % i
                pass
    
    return genre


if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option("-f", "--from", dest="fr", help="start from this ID", type="int")
    parser.add_option("-t", "--to", dest="to", help="go up to this ID", type="int")
    parser.add_option("-x", "--extras", dest="extra", help="get more information", action="store_true")

    (options, args) = parser.parse_args()

    conn = sqlite3.connect('netflix_genres.sqlite')
    c = conn.cursor()

    for i in range(options.fr, options.to):
        genre = get_genre(i, options.extra)
        conn.commit()

        if genre:
            print "%s (%s)" % (i, genre)
        time.sleep(0.2)

    conn.close()
