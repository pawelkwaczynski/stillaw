<p align="center">
  <img src="assets/banner-1280x640.png" alt="Stillaw" width="640">
</p>

<p align="center">
  <a href="https://pypi.org/project/stillaw/"><img alt="PyPI" src="https://img.shields.io/pypi/v/stillaw?color=102A43&labelColor=F6F5F1"></a>
  <a href="LICENSE"><img alt="Licencja" src="https://img.shields.io/badge/licencja-MIT-102A43?labelColor=F6F5F1"></a>
  <img alt="Testy" src="https://img.shields.io/badge/testy-64%20offline-102A43?labelColor=F6F5F1">
  <img alt="Bez LLM" src="https://img.shields.io/badge/model%20j%C4%99zykowy-%C5%BCaden-C58A1C?labelColor=F6F5F1">
</p>

<p align="center">
  <b>Czy to nadal jest prawo?</b><br>
  <a href="#instalacja">Instalacja</a> ·
  <a href="#jak-uzywac">Jak używać</a> ·
  <a href="#co-potrafi-a-czego-nie">Co potrafi, a czego nie</a> ·
  <a href="README.md">🇬🇧 in English</a>
</p>

---

Podajesz ustawę (adres z Dziennika Ustaw, identyfikator ELI albo tytuł) i datę, a Stillaw mówi,
czy tekst jednolity nadal obowiązywał tego dnia, która nowelizacja go wyprzedziła, od kiedy,
i **cytuje przepis, z którego odczytał datę**. Żadnego modelu językowego: wszystko pochodzi
z oficjalnego API ELI Dziennika Ustaw (api.sejm.gov.pl), deterministycznie, z sumą kontrolną odpowiedzi.

> **Z 89 polskich tekstów jednolitych sprawdzonych 24.08.2026 aż 57 nie było już prawem obowiązującym.**
> Tekst może być nieaktualny i jednocześnie być najnowszym, jaki opublikowano.

## Dla kogo

- **Prawnicy i działy prawne**, którzy muszą wiedzieć, czy tekst pobrany z bazy kwartał temu
  nadal obowiązuje, zanim trafi do pisma.
- **Każdy, kto buduje asystenta prawniczego.** Warstwa wyszukiwania, która zwraca najnowszy
  tekst jednolity, to nie to samo co warstwa zwracająca obowiązujące prawo. Stillaw mówi, co masz.
- **Compliance i zespoły regulacyjne**, które śledzą, co się zmienia i od kiedy, łącznie
  ze zmianami ogłoszonymi, ale jeszcze nieobowiązującymi.
- **Badacze**, którym potrzebna jest data, którą da się obronić, razem z przepisem, z którego pochodzi.

## Instalacja

```
pip install stillaw
```

Python 3.11 lub nowszy, wyłącznie biblioteka standardowa. Dwa zewnętrzne programy: `curl`
jako awaryjne wyjście, gdy Python nie ufa certyfikatowi API, oraz `pdftotext` (poppler),
bo ELI udostępnia akty zmieniające tylko w PDF.

## Jak używać

```
stillaw check "Dz.U. 2025 poz. 277" --as-of 2026-09-18
```

```
Dz.U. 2025 poz. 277  Kodeks pracy  (tekst jednolity ogłoszony 2025-03-06)
status na 2026-09-18: SUPERSEDED od 2025-12-13
wyprzedzony przez: DU/2025/1661  Ustawa o układach zbiorowych pracy
nowelizacji po tym tekście: 5
  DU/2025/807    ogłoszona 2025-06-23  w mocy od 2025-12-24  po 6 miesiącach
      podstawa: wchodzi w życie po upływie 6 miesięcy od dnia ogłoszenia.
  [... i kolejne, każda ze swoim przepisem końcowym ...]
```

Ostatnia linia każdego wpisu jest w tym najważniejsza: to dosłowny przepis, z którego wyliczono
datę. Można sprawdzić, czy program się nie pomylił.

Przyjmowane zapisy: `Dz.U. 2024 poz. 1251`, `Dz. U. z 2024 r. poz. 1251`, `DU/2024/1251`,
albo tytuł, na przykład `Kodeks pracy`. Powołanie aktu pierwotnego jest przekierowywane
na jego najnowszy tekst jednolity.

Przełącznik `--json` zwraca to samo jako dane, do wpięcia we własny program.

## Cztery możliwe statusy

| status | znaczenie |
|---|---|
| `current` | po tekście jednolitym nie ogłoszono żadnej nowelizacji |
| `superseded` | co najmniej jedna nowelizacja już obowiązuje na podaną datę |
| `vacatio_legis` | nowelizacje są, ale żadna jeszcze nie weszła w życie. Tekst **nadal jest prawem** |
| `undetermined` | jest nowelizacja, której daty nie dało się ustalić. **Nigdy nie raportujemy tego jako `current`**, bo tekst może już być wyprzedzony, a my po prostu nie wiemy |

Czwarty status jest tym uczciwym. Program, który nie umie czegoś ustalić, ma to powiedzieć,
a nie zgadywać.

## Co potrafi, a czego nie

Czyta przepis końcowy każdego aktu zmieniającego, razem z wyjątkami odsuwającymi całe artykuły
albo rozdziały na inną datę. Wie, który artykuł aktu zmieniającego dotyka Twojej ustawy, więc
podaje datę dla Twojej ustawy, a nie dla aktu jako całości.

Czego nie robi:

- **Działa na poziomie aktu, nie przepisu.** Wyjątek odsuwający jeden punkt artykułu jest
  odnotowany, ale status idzie za datą podstawową. Czy zmienił się akurat ten paragraf,
  który Cię interesuje, ta wersja nie odpowiada.
- **Nie zgaduje.** Daty wyznaczone przez inną ustawę, przez rozporządzenie albo przez wyrok
  Trybunału Konstytucyjnego trafiają do `undetermined`.
- **Obejmuje Dziennik Ustaw.** Monitor Polski, prawo unijne i prawo miejscowe są poza zakresem.
- **Nie ocenia, czy zmiana jest istotna.** Poprawka jednego słowa i przepisanie całego artykułu
  tak samo czynią tekst wyprzedzonym.

## Zgłoszenia

Najbardziej przydatne zgłoszenie to ustawa, dla której status wychodzi źle: wklej adres, datę
i to, czego się spodziewałeś. Parser powstał z przepisów napotkanych w praktyce, więc każda
niezrozumiana klauzula to realna luka.

Jeśli Stillaw oszczędził Ci jednego błędnego powołania przepisu, zostaw ⭐. Gwiazdki decydują
o tym, czy narzędzie zobaczy następna osoba, która go potrzebuje.

## Licencja

MIT. Copyright 2026 Paweł Kwaczyński.
