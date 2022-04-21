# autosylabusuj
Narzędzie wspomagające analizę i opiniowanie sylabusów UJ przysyłanych w PDF.


## Cele
Narzędzie służy do przetwarzania plików sylabusów przysyłanych w PDF do
zaopiniowania na tabelę w CSV zawierającą wybrane informacje.
Taką tabelę podsumowującą można potem przetworzyć np. importując ją do
arkusza kalkulacyjnego.

Informacje wybrane do ekstrakcji to te, które w doświadczeniu często
zawierają sprzeczności:
- pole *forma weryfikacji uzyskanych efektów uczenia się*
- warunki zaliczenia zajęć, przedmiotu
- *Wymagania wstępne i dodatkowe*

W chwili obecnej, generowana jest tabela o szerokości 26 kolumn (A-Z).

- strona : numer strony, na której zaczyna się sylabus danego przedmiotu
- nazwa : przedmiotu
- formaWeryfikacji : informacja zawarta w tabeli na pierwszej stronie pod tekstem "Forma weryfikacji uzyskanych efektów uczenia się"
----
Następne kolumny odnoszą się do poszczególnych rodzajów zajęć dydaktycznych
i działają na zasadzie "one-hot encoding"
[(kod 1 z n wg polskiej wiki)](https://pl.wikipedia.org/wiki/Kod_1_z_n).
W przypadku, gdy w tabeli pod "Informacje dodatkowe" wystąpi dany rodzaj
zajęć, ale ma puste pole "Formy zaliczenia" lub "Warunki zaliczenia przedmiotu",
skrypt powinien umieścić w tabeli raportu tekst ostrzegawczy `<!BRAK!>`.
- wykład
- wyk_formaZal
- wyk_warunkiZal
- ćwiczenia
- ćwi_formaZal
- ćwi_warunkiZal
- konwersatorium
- kon_formaZal
- kon_warunkiZal
- seminarium
- sem_formaZal
- sem_warunkiZal
- laboratoria
- lab_formaZal
- lab_warunkiZal
- pracownia
- pra_formaZal
- pra_warunkiZal
- praktyki
- praktyki_formaZal
- praktyki_warunkiZal

Skrypt zna i potrafi zakodować tylko wspomniane wyżej rodzaje zajęć;
w przypadku wystąpienia innych, powinien umieścić adnotację pod "inne uwagi".

----
- wymagania wstępne i dodatkowe : tekst występujący pod nagłówkiem
- inne uwagi : dodatkowe adnotacje umieszczone przez skrypt, w szczególności
  w celu zakomunikowania ostrzeżenia lub niekrytycznego błędu.


## Zależności
- Python 3
- mupdf
- PyQuery i jego zależności


## Stosowanie
1. Pozyskaj plik PDF z sylabusem do przetworzenia.
2. Użyj `mutool draw` do konwersji dokumentu na HTML: `mutool draw -o konwert.html sylabus.pdf`
3. Wywołaj narzędzie z terminala/wiersza poleceń lub po zaimportowaniu
i wywołaniu `main()` z odpowiednimi argumentami (lista argv).
4. Importuj plik raportu (tabela CSV) do arkusza kalkulacyjnego w celu dalszej analizy.


## Użycie z wiersza poleceń (opcje)

    usage: [-h] [-v] [-o nazwa_pliku_wyj] nazwa_plik_wej

    Narzędzie wspomagające analizę sylabusów w plikach PDF, po konwersji do pliku
    HTML z użyciem `mutool draw` z zestawu MuPDF.

    positional arguments:
      nazwa_plik_wej      Nazwa pliku wejściowego.

    optional arguments:
      -h, --help          show this help message and exit
      -v                  Pokaż więcej informacji podczas przetwarzania (na razie
                          słabo zaimplementowane).
      -o nazwa_pliku_wyj  Nazwa pliku wyjściowego.

Skrypt może również zostać wywołany po zaimportowaniu do innego programu, poprzez
przekazanie do funkcji `main()` listy argumentów:
```python
import autosylabusuj

autosylabusuj.main(["autosylabusuj", "-h", "-o", "plik_wyj.csv", "plik_wej.csv"])
```

## Ograniczenia
Cały skrypt polega na dokumencie HTML generowanym w wyniku
konwersji wejściowego pliku PDF przez `mutool draw`.

Program jest pisany na podstawie inżynierii odwrotnej tego dokumentu HTML,
który szczęśliwie ma dość regularną, choć słabo oznaczoną strukturę.
Stara się odnajdywać motywy występujące w tym "tłumaczeniu".
Jest to rozwiązanie dalekie od idealnego i wysoce podatne na perturbacje
wskutek licznych niewypowiedzianych założeń,
niemniej trudno wymyślić cokolwiek lepszego, zaczynając od dokumentu PDF.

- *Warunki wstępne i dodatkowe* rozbite na osobne strony mogą zostać ucięte.
- Powtarzające się sylabusy przedmiotów mogą wywoływać problemy, ktore skrypt będzie sygnalizował. Użycie opcji `-v` może okazać się wówczas pomocne.
