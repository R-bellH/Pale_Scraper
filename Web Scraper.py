import requests
import bs4
from bs4 import BeautifulSoup
from ebooklib import epub

# Global
currentArcTitle = ""
currentArcNumber = -1
book, extras = None, None
arcs = []
arcs_titles = []
spine = ["nav"]
x = 0


def main():
    print("Scraping...")
    global book, currentArcTitle, currentArcNumber, arcs_titles
    initializeEpubMetadata()
    # Access Table of Contents
    URLTableOfContents = "https://palewebserial.wordpress.com/table-of-contents/"
    page = requests.get(URLTableOfContents)

    soup = BeautifulSoup(page.content, "html.parser")  # Table of Contents

    entryResults = soup.find("div", class_="entry-content")

    for child in entryResults.find_all(recursive=False):
        # # if child contains <p style="padding-left: 40px;">, then it's an arc title
        if child.name == 'p':
            if child.get('style') is None:
                currentArcTitle = child.text
                arcs_titles.append(currentArcTitle)
                currentArcNumber += 1
            else:
                iterateChapters(child)
    generateBook()
    print("Epub file has been generated!")


def initializeEpubMetadata():
    global book
    book = epub.EpubBook()
    book.set_title("Pale")
    book.add_author("Wildbow")


def iterateChapters(chapters):
    chaptersSoup = BeautifulSoup(str(chapters),
                                 "html.parser")  # Contains a list (not the Python kind of list) of chapters of a given book number
    titles = []
    for br in chaptersSoup.find_all("br"):
        chapter_title = br.previous_sibling
        if type(chapter_title) == bs4.element.Tag:
            chapter_title = chapter_title.text
        titles.append(clean_title(chapter_title))

    for i, chapter in enumerate(chaptersSoup.find_all("a")):
        chapter_title = clean_title(chapter.text) + " - " + titles[i]
        chapter_url = chapter.get('href')
        extractChapter(chapter_title, chapter_url)


def extractChapter(title, url):
    global book, extras, x
    chapterPage = requests.get(url)
    chapterSoup = BeautifulSoup(chapterPage.content, "html.parser")
    content = chapterSoup.find("div", class_="entry-content")  # Chapter main text body
    for s in chapterSoup.select("div", id="jp-post-flair"): s.extract()  # Remove footer buttons
    for s in content.find_all("strong"): s.extract()  # Remove next/previous chapter buttons
    for s in content.find_all("h1"): s.extract()  # Remove title
    appendChapterToBook(content, title)


def appendChapterToBook(content, title):
    global book, spine, x, arcs, currentArcNumber
    epubChapter = epub.EpubHtml(title=title, file_name=str(x) + ".xhtml", lang='en')
    epubChapter.content = "<h2>" + title + "</h2>" + str(content).replace('<div class="entry-content">\n', "").replace(
        '\n </div>', "")
    book.add_item(epubChapter)
    spine.append(epubChapter)
    if len(arcs) <= currentArcNumber:
        arcs.append([])
    arcs[currentArcNumber].append(epubChapter)
    x += 1
    print(title + " OK!")


def generateBook():
    global book, arcs, spine, arcs_titles
    print("Generating EPUB file...")
    toc = []
    for i, arc in enumerate(arcs):
        toc.append((epub.Section(arcs_titles[i]), arc))
    book.toc = tuple(toc)
    book.spine = spine
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    epub.write_epub("Pale.epub", book, {})


def clean_title(text):
    if text is None:
        return ""
    # if text dont contains "-" return it
    if "–" in text:
        text = text.split("–")[1]
    return text.replace(" ", "")


main()
