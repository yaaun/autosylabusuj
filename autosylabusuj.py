# -*- coding: utf-8 -*-

"""
Skrypt do automatyzacji analizy sylabusów
=========================================
Ten skrypt ma za zadanie wspomóc samorząd w analizie sylabusów. Jest
to rozwiązanie *ad hoc* dostosowane do konkretnego formatu dokumentów
sylabusowych przesyłanych najczęściej w PDF przez kierowników studiów do
zaopiniowania. Toolchain jest z pewnością kruchy, polega na wielu
niewypowiedzianych założeniach i może wymagać znacznych zmian w przyszłości.

Autor oryginalny: Tomasz Kuliński, 18. kwietnia 2022

Stosowanie
----------
Użyj narzędzia `MuPDF <https://mupdf.com/releases/index.html>`_ do zamiany
pliku PDF na HTML (testowano z MuPDF 1.16.0 i 1.19.1 z identycznym rezultatem)
::

    mutool draw -o ZMN_2_S.html '.\22_UJ.WFAI_ZMN_2_S_20220403122547.pdf'

Spójrz na plik HTML w przeglądarce, czy wygląda pół-rozsądnie. Jeśli tak,
prawdopodobnie można użyć tego pliku jako wejściowego do tego narzędzia.


Uwagi dla programistów
----------------------
Wszystkie funkcje w tym module zaczynające się na ``pgq_`` biorą obiekt
PyQuery reprezentujący ``<div>`` definiujący stronę w wyjściowym HTML od
mutool draw.

Poszczególne funkcje ``pgq_`` stosują różne, najczęściej określone *ad hoc*
"kotwice" w dokumencie, które stanowią punkty referencyjne dla użytecznych
informacji - zazwyczaj są to nagłówki tabel i inne stałe elementy w kartach
opisów przedmiotów.
"""

import argparse
import configparser
import csv
import re
import sys
import warnings

from pyquery import PyQuery


def pgq_wyciagnijNazwePrzedmiotu(pgq):
    kotwica = pgq.children("img")
    poSelector = "p:contains('Karta opisu przedmiotu')"
    elemPoKotwicy = kotwica.nextAll()

    linieTyt = []

    for el in elemPoKotwicy:
        elq = PyQuery(el)

        if elq.is_(poSelector):
            return " ".join(linieTyt)
        else:
            linieTyt.append(elq.text())


def pgq_wyciagnijSciezke(pgq):
    kotwica = pgq.children("p > b") \
        .filter(lambda i, elem: PyQuery(elem).text() == "Ścieżka").parents()[-1]
    nastepny = PyQuery(kotwica).next()

    return nastepny.text() # to powinna być nazwa ścieżki.


def pgq_wyciagnijFormeWeryfikacji(pgq):
    nastepnyElem = pgq.children("p:contains('Forma weryfikacji uzyskanych efekt') + p")
    return nastepnyElem.text()


def pgq_wyciagnijSposobyGodzinyRealizacji(pgq):
    kotwica = pgq.children("p:contains('Sposób realizacji i godziny zajęć')")
    stoper = kotwica.nextAll().filter("p:contains('Liczba')")[0]
    bufor = []

    for elem in kotwica.nextAll():
        pqelem = PyQuery(elem)
        if elem == stoper: # To nie jest błąd, że tu nie ma elementu owiniętego w PyQuery.
            break

        bufor.append(pqelem.text())

    bufor = " ".join(bufor)
    sposoby_i_godziny = re.findall(r"(\w{4,40}): (\d{1,3})", bufor) # Parsing typu 'klucz: wartość'
    # Struktura sposoby_i_godziny będzie listą 2-tupli (par).
    return dict(sposoby_i_godziny)

def str_sposobyGodzinyRealizacji(sposoby_i_godziny):
    return ", ".join(map(lambda kv: f"{kv[0]}: {kv[1]}", sposoby_i_godziny.items()))


def wyciagnijStyleLeft(pqelem):
    """
    Wyciągnij przesunięcie 'left' przy absolutnym pozycjonowaniu specyfikowanym
    w atrybucie 'style'.

    Parameters
    ----------
    pqelem : PyQuery
        Element do analizy.

    Returns
    -------
    leftstr : str
        Długość w jednostkach CSS, np. '123pt'.

    """
    leftstr = re.search("left\\s*:\\s*(\d+(?:pt|px|cm));?", pqelem.attr.style)[1]
    return leftstr

def cssDlwPt(cssdl):
    """
    Zamienia jednostkę długości absolutnej w formacie CSS na liczbowę będącą
    długością w pt (72 pt = 1 inch tzn. cal).

    Parameters
    ----------
    cssdl : str
        Długość absolutna dopuszczalna przez CSS, np. `

    Returns
    -------
    float
        Długość w pt.

    """
    unitSymbMatch = re.search("[a-z]{1,2}", cssdl)
    unitSymb = unitSymbMatch[0]
    preUnitDigits = cssdl[0:unitSymbMatch.start()]
    numval = float(preUnitDigits)

    if unitSymb == "pt":
        return numval
    elif unitSymb == "px":
        return numval * 72 / 96
    elif unitSymb == "mm":
        return numval / 25.4 * 72
    elif unitSymb == "cm":
        return numval / 2.54 * 72
    elif unitSymb == "in":
        return numval * 72
    else:
        raise ValueError(f"nieznana jednostka długości '{unitSymb}'")


def pgq_wyciagnijWarunkiZaliczenia(pgq, kotwica, verbosity=0):
    nastepne = kotwica.nextAll()
    pierwszyPo = None

    try:
        # Potrzebne na przypadki, kiedy cała treść przeleje się na kolejną stronę
        # i nie ma żadnej treści na tej stronie (poza nagłówkiem)
        pierwszyPo = PyQuery(nastepne[0])
    except IndexError as e:
        return [] # Pusta tabela nie powinna wyrządzać dalszych szkód przy łączeniu.

    # Inicjalizacja.
    leftPosPt = [ cssDlwPt(wyciagnijStyleLeft(pierwszyPo)), 0, 0 ]
    bufory = [ [pierwszyPo.text()], [], [] ]
    kol = 0

    tabelaWarZal = []

    for elem in nastepne[1:]:
        elemq = PyQuery(elem)
        leftStr = wyciagnijStyleLeft(elemq)
        leftPt = cssDlwPt(leftStr)

        # Kod zakłada, że akapity <p> są wielo- lub jednoliniowe, wyrównane
        # absolutnie do lewej i ułożone w kodzie HTML w kolejności linie
        # góra do dołu, akapity prawa do lewej (kolumny tabeli),
        # rząd tabeli z góry do dołu.
        if leftPt > leftPosPt[kol]:
            # Przejście do następnej kolumny.
            kol += 1
            leftPosPt[kol] = leftPt
        elif leftPt < leftPosPt[kol]: # Jakaś nieciągłość.
            kol = 0 # Reset kolumny do pierwszej.
            if leftPt == leftPosPt[kol]:
                tabelaWarZal.append( (" ".join(bufory[0]), " ".join(bufory[1]),
                                     " ".join(bufory[2])) ) # Wypis buforów do tabeli wyjściowej.
                # Kontynuuj z przetwarzaniem kolejnego rzędu tabeli, przy
                # założeniu, że wyrównanie do lewej w kolejnych rzędach
                # jest identyczne, jak w pierwszym.
                bufory = [[], [], []] # W tym celu potrzeba nowych buforów na tekst.
            else:
                # Coś jest inaczej z położeniem poziomym i nie pasuje, przerwij.
                break

        bufory[kol].append(elemq.text())

    # "Sprzątanie" jeśli skanowanie dotarło do końca strony.
    tabelaWarZal.append( (" ".join(bufory[0]), " ".join(bufory[1]),
                         " ".join(bufory[2])) )

    return tabelaWarZal


def pgq_wyciagnijWymaganiaWstep(pgq):
    kotwica = pgq.children("p:contains('Wymagania wstępne i dodatkowe')")
    # Generalnie to powinna być ostatnia sekcja, a nawet jeśli nie jest, to
    # można skorzystać z już wypróbowanej metody wykrywania "cofnięcia wózka"
    # aby znaleźć koniec.

    if not kotwica:
        raise RuntimeError("brakuje kotwicy dla szukania 'Wymagania wstępne i dodatkowe'")

    bufor = []
    nastepne = kotwica.nextAll()
    pierwszyPo = PyQuery(nastepne[0])

    leftPtOryg = cssDlwPt(wyciagnijStyleLeft(pierwszyPo))
    bufor.append(pierwszyPo.text())

    for p in nastepne[1:]:
        p = PyQuery(p)
        leftPt = cssDlwPt(wyciagnijStyleLeft(p))

        if leftPt >= leftPtOryg:
            # Ciąg dalszy akapitu, rozbitego na osobne linijki.
            bufor.append(p.text())
        else:
            # Położenie od lewej się cofnęło, pewnie zaczęło się coś innego.
            break

    return " ".join(bufor)


def pgq_wyciagnijNumerStrony(pgq):
    return int(re.match("page(\\d+)", pgq.attr.id)[1])


def warzal_PyQuery(nazwa_plik_wej, verbosity=0):
    def isSylabusPage(index, div):
        return bool(PyQuery(div).children("p:first-child").text() == "Sylabusy")

    if verbosity >= 1:
        print(f"nazwa_plik_wej = {nazwa_plik_wej}")

    pq = PyQuery(filename=nazwa_plik_wej)

    sylabusPgs = pq("div").filter(isSylabusPage)

    nazwaPrzedm = None # Zmienna potrzebuje persystencji pomiędzy obrotami pętli po stronach.
    stronaPocz = 0
    warZalicz = dict()

    for pg in sylabusPgs:
        pgq = PyQuery(pg)
        nrStrony = pgq_wyciagnijNumerStrony(pgq)

        # Trzeba stwierdzić, czy to jest pierwsza strona przedmiotu czy nie.
        # Jesli tak, trzeba wyciągnąć nazwę przedmiotu.
        if pgq.children("img"): # w oparciu o obrazek nad tytułem
            nazwaPrzedm = pgq_wyciagnijNazwePrzedmiotu(pgq)
            #print(repr(nazwaPrzedm)) # Żeby dodać cudzysłowy dla klarownosci.
            sciezka = pgq_wyciagnijSciezke(pgq)
            stronaPocz = pgq_wyciagnijNumerStrony(pgq)

            if verbosity >= 1:
                print(f"Przedmiot '{nazwaPrzedm}', ścieżka '{sciezka}', strona {stronaPocz}")

            if sciezka != "-":
                # Jeśli ścieżka jest inna niż domyślny placeholder '-', to
                # uzupełnij nazwę przedmiotu ścieżką przez postfix
                # w nawiasach kwadratowych.
                nazwaPrzedm = nazwaPrzedm + f" [{sciezka}]"

            formaWeryf = pgq_wyciagnijFormeWeryfikacji(pgq)
            sposobyGodziny = pgq_wyciagnijSposobyGodzinyRealizacji(pgq)
            sposobyGodziny_str = str_sposobyGodzinyRealizacji(sposobyGodziny)

            # Sprawdź czy istnieje taki przedmiot w słowniku, aby uniknąć nadpisywania
            if nazwaPrzedm not in warZalicz:


                warZalicz[nazwaPrzedm] = {"formaWeryfikacji": formaWeryf,
                                      "strona": stronaPocz,
                                      "sposobyRealizacji": sposobyGodziny_str,
                                      "_sposobyRealizacji": sposobyGodziny}
            else:
                warnings.warn(f"powtórzył się sylabus przedmiotu o tej samej nazwie "
                              f"'{nazwaPrzedm}'")
        elif nazwaPrzedm and pgq.children("p:contains('Rodzaj zajęć')") and \
            pgq.children("p:contains('Formy zaliczenia')") and \
            pgq.children("p:contains('Warunki zaliczenia przedmiotu')"):
            # Trafilismy na tabelę "Informacje rozszerzone", gdzie są (powinny być)
            # warunki zaliczenia przedmiotu.
            # Może to być jako `elif`, bo ta tabela nigdzie* nie występuje
            # (*nie widziałem żeby występowała) na tej samej stronie, co
            # tytuł przedmiotu - zatem nie dojdzie do interferencji i wykluczania
            # się.

            # Wprowadzenie ostrzeżenia na wypadek, gdyby przypadek 'if' powyżej
            # nie chwycił kolejnego przedmiotu wystarczająco szybko.
            sylabusDlStron = nrStrony - stronaPocz
            if sylabusDlStron > OstrzezGdySylabusDluzszyNiz_strony:
                warnings.warn(f"sylabus przedmiotu {nazwaPrzedm} (od strony {stronaPocz}, "
                              f"na stronie {nrStrony}) jest dłuższy niż zwykle "
                             f"(spodziewano się max {OstrzezGdySylabusDluzszyNiz_strony} "
                             f"stron, stwierdzono {sylabusDlStron}) - "
                             "możliwe, że nastąpiła ucieczka przy czytaniu.")

            # Lepszą "kotwicą" jest nagłówek tabeli, ponieważ jest powtarzany
            # w przypadkach, gdy treści się "rozleją" na kolejne strony.
            kotwica = pgq.children("p:contains('Warunki zaliczenia przedmiotu')")
            tabelaWarZal = pgq_wyciagnijWarunkiZaliczenia(pgq, kotwica)

            # Spłaszczenie struktury tabeli warunków zaliczenia.
            for rodzajZaj, formaZal, warunkiZal in tabelaWarZal:
                # Powinien już istnieć dict, żeby to wszystko umieścić.

                skrotRodzaju = skrocRodzajZaj(rodzajZaj)

                # Sprawdź, czy istnieje taka forma zajęć wśród znanych.
                if rodzajZaj in KolumnyTabeliRaportu:
                    warZalicz[nazwaPrzedm][rodzajZaj] = TSV_PRAWDA
                    warZalicz[nazwaPrzedm][skrotRodzaju + "_formaZal"] = formaZal or "<!BRAK!>"
                    warZalicz[nazwaPrzedm][skrotRodzaju + "_warunkiZal"] = warunkiZal or "<!BRAK!>"
                else:
                    warZalicz[nazwaPrzedm]["inne uwagi"] = f"Napotkano nieznany rodzaj zajęć '{rodzajZaj}'. "\
                        f"Forma zaliczenia: '{formaZal}', warunki zaliczenia: '{warunkiZal}'"
                    warnings.warn(f"Napotkano nieznany rodzaj zajęć '{rodzajZaj}' na stronie {pgq_wyciagnijNumerStrony(pgq)}")

        # To może być zarówno na tej samej stronie, co formy i warunki
        # zaliczenia, ale może równie dobrze wystąpić na osobnej stronie.
        # Lepiej sprawdzić niezależnie od wcześniejszych przypadków.
        if nazwaPrzedm and pgq.children("p:contains('Wymagania wstępne i dodatkowe')"):
            # Jest tytuł. Na razie na tym polegamy, choć niestety nie jest
            # wykluczone, że teoretycznie możliwe jest przelanie się tekstu
            # na kolejną stronę bez powtórzenia tytułu - wtedy będzie kiepsko :(
            #print(pgq.children("p:contains('Wymagania wstępne i dodatkowe')"))
            warZalicz[nazwaPrzedm]["wymagania wstępne i dodatkowe"] = pgq_wyciagnijWymaganiaWstep(pgq)

    # Sprawdzanie wewnętrznej spójności:
    # np. sposoby realizacji vs tabela z warunkami zaliczenia
    for nazwaPrzedm, przedmDict in warZalicz.items():
        for sposobRealiz in przedmDict["_sposobyRealizacji"]:
            try:
                if not przedmDict[sposobRealiz] == TSV_PRAWDA:
                    warnings.warn("niespójność sposobów realizacji przedmiotu z "
                              "tabelą form zaliczenia zajęć")
            except KeyError as e:
                warnings.warn("niespójność sposobów realizacji przedmiotu z "
                          "tabelą form zaliczenia zajęć w związku z nieznanym "
                          f"typem zajęć {str(e)}")

    return warZalicz


KolumnyTabeliRaportu = ["strona", "nazwa", "formaWeryfikacji",
                        "sposobyRealizacji",
                        "wykład", "wyk_formaZal", "wyk_warunkiZal",
                        "ćwiczenia", "ćwi_formaZal", "ćwi_warunkiZal",
                        "konwersatorium", "kon_formaZal", "kon_warunkiZal",
                        "seminarium", "sem_formaZal", "sem_warunkiZal",
                        "laboratoria", "lab_formaZal", "lab_warunkiZal",
                        "pracownia", "pra_formaZal", "pra_warunkiZal",
                        "projekt", "proj_formaZal", "proj_warunkiZal",
                        "warsztaty", "war_formaZal", "war_warunkiZal",
                        "praktyki", "praktyki_formaZal", "praktyki_warunkiZal",
                        "wymagania wstępne i dodatkowe", "inne uwagi"]
OstrzezGdySylabusDluzszyNiz_strony = 4
TSV_PRAWDA = "TRUE"

def skrocRodzajZaj(rodzajZaj):
    if rodzajZaj == "praktyki":
        return rodzajZaj
    else:
        return rodzajZaj[0:3]


def warzal_formatWyjsciaTSV(warzalDict, args):
    warzalDictRows = map(lambda kv: {"nazwa": kv[0], **kv[1]},
                         warzalDict.items())

    if not args.o:
        args.o = args.nazwa_plik_wej + "raport.tsv"

    with open(args.o, "wt", newline="", encoding="utf-8") as csvReport:
        reportWriter = csv.DictWriter(csvReport, KolumnyTabeliRaportu,
                                      dialect="excel-tab", extrasaction="ignore")
        reportWriter.writeheader()
        reportWriter.writerows(warzalDictRows)



def warzal_formatWyjsciaINI(warzalDict, args):
    confpars = configparser.ConfigParser(interpolation=None)
    confpars.optionxform = lambda x: x

    for nazwaPrzedm, przedmDict in warzalDict.items():
        # Pierwsza pętla idzie po przedmiotach.
        for nazwaWlasc, wartoscWlasc in przedmDict.items():
            # Druga pętla idzie po właściwościach poszczególnych przedmiotów.
            # Właściwości zaczynające się od podkreślenia `_` są uznawane
            # za prywatne (do wewnętrznego użytku) dla programu i nie będą
            # wstawiane do pliku.
            if not nazwaWlasc.startswith("_"):
                confpars[nazwaPrzedm][nazwaWlasc] = wartoscWlasc

    if not args.o:
        args.o = args.nazwa_plik_wej + "raport.ini"

    with open(args.o, "wt", encoding="utf-8") as plikWyj:
        confpars.write(plikWyj)


def main(argv):
    parser = argparse.ArgumentParser(
            description="Narzędzie wspomagające analizę sylabusów w plikach PDF, "
            "po konwersji do pliku HTML z użyciem `mutool draw` z zestawu MuPDF."
        )

    parser.add_argument("nazwa_plik_wej", type=str, help="Nazwa pliku wejściowego.")
    parser.add_argument("-v", action="count", help="Pokaż więcej informacji podczas "
                        "przetwarzania (na razie słabo zaimplementowane).", default=0)
    parser.add_argument("-o", type=str, help="Nazwa pliku wyjściowego.",
                        metavar="nazwa_pliku_wyj")
    parser.add_argument("-f", dest="format", type=str, default="tsv",
                        help="Format pliku wyjściowego "
                        "(raportu) do wygenerowania. Domyślnie jest to tabela "
                        "tekstowa TSV (tab separated values), którą można łatwo "
                        "wkleić do arkusza kalkulacyjnego.")
    parser.add_argument("-t", dest="tryb", type=str, default="WarZal", help=""
                        "Tryb działania. Dopuszczalne wartości to: 'WarZal', "
                        "domyślna wartość to 'WarZal'.")
    #parser.add_argument("plik_wyj", type=argparse.FileType("wt"))
    args = parser.parse_args(argv[1:])

    # warzal = WarunkiZaliczeniaParser()

    # for lineno, line in enumerate(args.plik_wej):
    #     print(lineno)
    #     warzal.feed(line)

    warzalDict = warzal_PyQuery(args.nazwa_plik_wej, verbosity=args.v)
    if args.format.lower() in {"tsv", "csv"}:
        warzal_formatWyjsciaTSV(warzalDict, args)
    elif args.format.lower() in {"ini"}:
        warzal_formatWyjsciaINI(warzalDict, args)

if __name__ == "__main__":
    main(sys.argv)
