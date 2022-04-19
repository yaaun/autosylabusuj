# autosylabusuj
Narzędzie wspomagające analizę i opiniowanie sylabusów UJ przysyłanych w PDF.


## Cele
Narzędzie służy do przetwarzania plików sylabusów przysyłanych w PDF do
zaopiniowania na tabelę w CSV zawierającą wybrane inforamcje.
Taką tabelę podsumowującą można potem przetworzyć np. importując ją do
Excela.

Informacje wybrane do ekstrakcji to te, które w doświadczeniu często
zawierają sprzeczności:
- pole *forma weryfikacji uzyskanych efektów uczenia się*
- warunki zaliczenia zajęć, przedmiotu
- *Wymagania wstępne i dodatkowe*

W chwili obecnej, generowana jest tabela o szerokości 26 kolumn (A-Z).


## Zależności
- mupdf
- PyQuery i jego zależności


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
