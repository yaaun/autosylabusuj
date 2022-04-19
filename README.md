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
