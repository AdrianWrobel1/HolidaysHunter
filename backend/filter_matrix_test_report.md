# Raport z Testu Kombinacji Filtrów Live Import

## Podsumowanie Wyników Testu
- **Wszystkie przetestowane kombinacje**: 231
- **Liczba kombinacji 1-elementowych**: 11
- **Liczba kombinacji 2-elementowych**: 55
- **Liczba kombinacji 3-elementowych**: 165
- **Status ogólny**: ✅ SUKCES (100% PASS)
- **Wynik PASS**: **231** / 231 (100.0%)
- **Wynik FAIL**: **0** / 231

## Weryfikowane Zasady Logiczne
1. **Brak błędów backendu**: Przetwarzanie i filtrowanie zapytań nie wyrzuca wyjątków SQL/Python ani błędów 500.
2. **Monotoniczność (Nesting property)**: Dodanie kolejnego filtra nie może zwiększyć liczby zwróconych wyników (`count(A + B) <= count(A)`).
3. **Brak fałszywych 0 (Non-zero matching)**: Jeśli w bazie danych/źródle istnieją rekordy spełniające wszystkie filtry w kombinacji, zapytanie nie może zwrócić 0 ofert.

## Tabela Wyników dla Wszystkich 231 Kombinacji Filtrów

| ID | Typ | Kombinacja Filtrów | Liczba Ofert | Status | Dokładna Przyczyna / Opis |
|---|---|---|---|---|---|
| 1 | 1-elementowa | `provider` | 15 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 2 | 1-elementowa | `country` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 3 | 1-elementowa | `region` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 4 | 1-elementowa | `airport` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 5 | 1-elementowa | `meal_type` | 6 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 6 | 1-elementowa | `stars` | 10 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 7 | 1-elementowa | `duration` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 8 | 1-elementowa | `adults` | 17 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 9 | 1-elementowa | `children` | 17 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 10 | 1-elementowa | `price` | 16 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 11 | 1-elementowa | `departure_date` | 17 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 12 | 2-elementowa | `provider + country` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 13 | 2-elementowa | `provider + region` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 14 | 2-elementowa | `provider + airport` | 5 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 15 | 2-elementowa | `provider + meal_type` | 4 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 16 | 2-elementowa | `provider + stars` | 10 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 17 | 2-elementowa | `provider + duration` | 5 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 18 | 2-elementowa | `provider + adults` | 15 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 19 | 2-elementowa | `provider + children` | 15 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 20 | 2-elementowa | `provider + price` | 14 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 21 | 2-elementowa | `provider + departure_date` | 15 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 22 | 2-elementowa | `country + region` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 23 | 2-elementowa | `country + airport` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 24 | 2-elementowa | `country + meal_type` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 25 | 2-elementowa | `country + stars` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 26 | 2-elementowa | `country + duration` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 27 | 2-elementowa | `country + adults` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 28 | 2-elementowa | `country + children` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 29 | 2-elementowa | `country + price` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 30 | 2-elementowa | `country + departure_date` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 31 | 2-elementowa | `region + airport` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 32 | 2-elementowa | `region + meal_type` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 33 | 2-elementowa | `region + stars` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 34 | 2-elementowa | `region + duration` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 35 | 2-elementowa | `region + adults` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 36 | 2-elementowa | `region + children` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 37 | 2-elementowa | `region + price` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 38 | 2-elementowa | `region + departure_date` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 39 | 2-elementowa | `airport + meal_type` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 40 | 2-elementowa | `airport + stars` | 5 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 41 | 2-elementowa | `airport + duration` | 4 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 42 | 2-elementowa | `airport + adults` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 43 | 2-elementowa | `airport + children` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 44 | 2-elementowa | `airport + price` | 6 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 45 | 2-elementowa | `airport + departure_date` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 46 | 2-elementowa | `meal_type + stars` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 47 | 2-elementowa | `meal_type + duration` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 48 | 2-elementowa | `meal_type + adults` | 6 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 49 | 2-elementowa | `meal_type + children` | 6 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 50 | 2-elementowa | `meal_type + price` | 6 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 51 | 2-elementowa | `meal_type + departure_date` | 6 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 52 | 2-elementowa | `stars + duration` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 53 | 2-elementowa | `stars + adults` | 10 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 54 | 2-elementowa | `stars + children` | 10 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 55 | 2-elementowa | `stars + price` | 9 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 56 | 2-elementowa | `stars + departure_date` | 10 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 57 | 2-elementowa | `duration + adults` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 58 | 2-elementowa | `duration + children` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 59 | 2-elementowa | `duration + price` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 60 | 2-elementowa | `duration + departure_date` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 61 | 2-elementowa | `adults + children` | 17 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 62 | 2-elementowa | `adults + price` | 16 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 63 | 2-elementowa | `adults + departure_date` | 17 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 64 | 2-elementowa | `children + price` | 16 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 65 | 2-elementowa | `children + departure_date` | 17 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 66 | 2-elementowa | `price + departure_date` | 16 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 67 | 3-elementowa | `provider + country + region` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 68 | 3-elementowa | `provider + country + airport` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 69 | 3-elementowa | `provider + country + meal_type` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 70 | 3-elementowa | `provider + country + stars` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 71 | 3-elementowa | `provider + country + duration` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 72 | 3-elementowa | `provider + country + adults` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 73 | 3-elementowa | `provider + country + children` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 74 | 3-elementowa | `provider + country + price` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 75 | 3-elementowa | `provider + country + departure_date` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 76 | 3-elementowa | `provider + region + airport` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 77 | 3-elementowa | `provider + region + meal_type` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 78 | 3-elementowa | `provider + region + stars` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 79 | 3-elementowa | `provider + region + duration` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 80 | 3-elementowa | `provider + region + adults` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 81 | 3-elementowa | `provider + region + children` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 82 | 3-elementowa | `provider + region + price` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 83 | 3-elementowa | `provider + region + departure_date` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 84 | 3-elementowa | `provider + airport + meal_type` | 1 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 85 | 3-elementowa | `provider + airport + stars` | 5 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 86 | 3-elementowa | `provider + airport + duration` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 87 | 3-elementowa | `provider + airport + adults` | 5 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 88 | 3-elementowa | `provider + airport + children` | 5 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 89 | 3-elementowa | `provider + airport + price` | 4 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 90 | 3-elementowa | `provider + airport + departure_date` | 5 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 91 | 3-elementowa | `provider + meal_type + stars` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 92 | 3-elementowa | `provider + meal_type + duration` | 1 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 93 | 3-elementowa | `provider + meal_type + adults` | 4 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 94 | 3-elementowa | `provider + meal_type + children` | 4 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 95 | 3-elementowa | `provider + meal_type + price` | 4 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 96 | 3-elementowa | `provider + meal_type + departure_date` | 4 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 97 | 3-elementowa | `provider + stars + duration` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 98 | 3-elementowa | `provider + stars + adults` | 10 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 99 | 3-elementowa | `provider + stars + children` | 10 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 100 | 3-elementowa | `provider + stars + price` | 9 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 101 | 3-elementowa | `provider + stars + departure_date` | 10 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 102 | 3-elementowa | `provider + duration + adults` | 5 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 103 | 3-elementowa | `provider + duration + children` | 5 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 104 | 3-elementowa | `provider + duration + price` | 5 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 105 | 3-elementowa | `provider + duration + departure_date` | 5 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 106 | 3-elementowa | `provider + adults + children` | 15 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 107 | 3-elementowa | `provider + adults + price` | 14 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 108 | 3-elementowa | `provider + adults + departure_date` | 15 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 109 | 3-elementowa | `provider + children + price` | 14 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 110 | 3-elementowa | `provider + children + departure_date` | 15 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 111 | 3-elementowa | `provider + price + departure_date` | 14 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 112 | 3-elementowa | `country + region + airport` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 113 | 3-elementowa | `country + region + meal_type` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 114 | 3-elementowa | `country + region + stars` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 115 | 3-elementowa | `country + region + duration` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 116 | 3-elementowa | `country + region + adults` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 117 | 3-elementowa | `country + region + children` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 118 | 3-elementowa | `country + region + price` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 119 | 3-elementowa | `country + region + departure_date` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 120 | 3-elementowa | `country + airport + meal_type` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 121 | 3-elementowa | `country + airport + stars` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 122 | 3-elementowa | `country + airport + duration` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 123 | 3-elementowa | `country + airport + adults` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 124 | 3-elementowa | `country + airport + children` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 125 | 3-elementowa | `country + airport + price` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 126 | 3-elementowa | `country + airport + departure_date` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 127 | 3-elementowa | `country + meal_type + stars` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 128 | 3-elementowa | `country + meal_type + duration` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 129 | 3-elementowa | `country + meal_type + adults` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 130 | 3-elementowa | `country + meal_type + children` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 131 | 3-elementowa | `country + meal_type + price` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 132 | 3-elementowa | `country + meal_type + departure_date` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 133 | 3-elementowa | `country + stars + duration` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 134 | 3-elementowa | `country + stars + adults` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 135 | 3-elementowa | `country + stars + children` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 136 | 3-elementowa | `country + stars + price` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 137 | 3-elementowa | `country + stars + departure_date` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 138 | 3-elementowa | `country + duration + adults` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 139 | 3-elementowa | `country + duration + children` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 140 | 3-elementowa | `country + duration + price` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 141 | 3-elementowa | `country + duration + departure_date` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 142 | 3-elementowa | `country + adults + children` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 143 | 3-elementowa | `country + adults + price` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 144 | 3-elementowa | `country + adults + departure_date` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 145 | 3-elementowa | `country + children + price` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 146 | 3-elementowa | `country + children + departure_date` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 147 | 3-elementowa | `country + price + departure_date` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 148 | 3-elementowa | `region + airport + meal_type` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 149 | 3-elementowa | `region + airport + stars` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 150 | 3-elementowa | `region + airport + duration` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 151 | 3-elementowa | `region + airport + adults` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 152 | 3-elementowa | `region + airport + children` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 153 | 3-elementowa | `region + airport + price` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 154 | 3-elementowa | `region + airport + departure_date` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 155 | 3-elementowa | `region + meal_type + stars` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 156 | 3-elementowa | `region + meal_type + duration` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 157 | 3-elementowa | `region + meal_type + adults` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 158 | 3-elementowa | `region + meal_type + children` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 159 | 3-elementowa | `region + meal_type + price` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 160 | 3-elementowa | `region + meal_type + departure_date` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 161 | 3-elementowa | `region + stars + duration` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 162 | 3-elementowa | `region + stars + adults` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 163 | 3-elementowa | `region + stars + children` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 164 | 3-elementowa | `region + stars + price` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 165 | 3-elementowa | `region + stars + departure_date` | 0 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 166 | 3-elementowa | `region + duration + adults` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 167 | 3-elementowa | `region + duration + children` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 168 | 3-elementowa | `region + duration + price` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 169 | 3-elementowa | `region + duration + departure_date` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 170 | 3-elementowa | `region + adults + children` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 171 | 3-elementowa | `region + adults + price` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 172 | 3-elementowa | `region + adults + departure_date` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 173 | 3-elementowa | `region + children + price` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 174 | 3-elementowa | `region + children + departure_date` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 175 | 3-elementowa | `region + price + departure_date` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 176 | 3-elementowa | `airport + meal_type + stars` | 1 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 177 | 3-elementowa | `airport + meal_type + duration` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 178 | 3-elementowa | `airport + meal_type + adults` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 179 | 3-elementowa | `airport + meal_type + children` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 180 | 3-elementowa | `airport + meal_type + price` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 181 | 3-elementowa | `airport + meal_type + departure_date` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 182 | 3-elementowa | `airport + stars + duration` | 2 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 183 | 3-elementowa | `airport + stars + adults` | 5 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 184 | 3-elementowa | `airport + stars + children` | 5 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 185 | 3-elementowa | `airport + stars + price` | 4 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 186 | 3-elementowa | `airport + stars + departure_date` | 5 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 187 | 3-elementowa | `airport + duration + adults` | 4 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 188 | 3-elementowa | `airport + duration + children` | 4 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 189 | 3-elementowa | `airport + duration + price` | 4 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 190 | 3-elementowa | `airport + duration + departure_date` | 4 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 191 | 3-elementowa | `airport + adults + children` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 192 | 3-elementowa | `airport + adults + price` | 6 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 193 | 3-elementowa | `airport + adults + departure_date` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 194 | 3-elementowa | `airport + children + price` | 6 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 195 | 3-elementowa | `airport + children + departure_date` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 196 | 3-elementowa | `airport + price + departure_date` | 6 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 197 | 3-elementowa | `meal_type + stars + duration` | 1 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 198 | 3-elementowa | `meal_type + stars + adults` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 199 | 3-elementowa | `meal_type + stars + children` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 200 | 3-elementowa | `meal_type + stars + price` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 201 | 3-elementowa | `meal_type + stars + departure_date` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 202 | 3-elementowa | `meal_type + duration + adults` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 203 | 3-elementowa | `meal_type + duration + children` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 204 | 3-elementowa | `meal_type + duration + price` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 205 | 3-elementowa | `meal_type + duration + departure_date` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 206 | 3-elementowa | `meal_type + adults + children` | 6 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 207 | 3-elementowa | `meal_type + adults + price` | 6 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 208 | 3-elementowa | `meal_type + adults + departure_date` | 6 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 209 | 3-elementowa | `meal_type + children + price` | 6 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 210 | 3-elementowa | `meal_type + children + departure_date` | 6 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 211 | 3-elementowa | `meal_type + price + departure_date` | 6 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 212 | 3-elementowa | `stars + duration + adults` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 213 | 3-elementowa | `stars + duration + children` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 214 | 3-elementowa | `stars + duration + price` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 215 | 3-elementowa | `stars + duration + departure_date` | 3 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 216 | 3-elementowa | `stars + adults + children` | 10 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 217 | 3-elementowa | `stars + adults + price` | 9 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 218 | 3-elementowa | `stars + adults + departure_date` | 10 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 219 | 3-elementowa | `stars + children + price` | 9 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 220 | 3-elementowa | `stars + children + departure_date` | 10 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 221 | 3-elementowa | `stars + price + departure_date` | 9 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 222 | 3-elementowa | `duration + adults + children` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 223 | 3-elementowa | `duration + adults + price` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 224 | 3-elementowa | `duration + adults + departure_date` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 225 | 3-elementowa | `duration + children + price` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 226 | 3-elementowa | `duration + children + departure_date` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 227 | 3-elementowa | `duration + price + departure_date` | 7 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 228 | 3-elementowa | `adults + children + price` | 16 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 229 | 3-elementowa | `adults + children + departure_date` | 17 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 230 | 3-elementowa | `adults + price + departure_date` | 16 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |
| 231 | 3-elementowa | `children + price + departure_date` | 16 | ✅ PASS | OK (Liczba ofert spójna, brak błędów backendu) |