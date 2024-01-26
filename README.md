# AnimeWorld Scraper

## ⚠ Disclaimer ⚠
Questo progetto è stato creato per scopi di studio e non per scopi commerciali. Inoltre, non mi assumo nessuna responsabilità per l'uso che ne farete.

Inoltre questo programma e' stato creato tanto per imparare quanto per divertimento, quindi non e' ottimizzato al massimo e potrebbe avere dei bug.

## Descrizione
Piccolo scraper in python fatto nel tempo libero che permette di:
- Prendere tutte le serie presenti su [AnimeWorld](https://www.animeworld.tv/)
- Importare tutte le serie in un unico json
- Scaricare tutti gli episodi di tutte le serie
- Scaricare tutti gli episodi di una singola serie

## Installazione

Disclaimer: Questo programma e' stato testato solo su Windows 10. Per farlo funzionare su altri sistemi operativi potrebbe essere necessario modificare il codice.

Per installare le dipendenze necessarie per questo progetto, esegui il seguente comando:

```bash
pip install -r requirements.txt
```

Inoltre e' necessario aver installato geckodriver nella cartella per poter utilizzare selenium, per farlo basta seguire [questa guida](https://selenium-python.readthedocs.io/installation.html#drivers) (il file geckodrive.exe va messo nella stessa cartella del file main.py).
Visto che sul sito sono presenti pubblicita' e darebbero problemi con selenium, e' importante scaricare questo adblocker per firefox: [uBlock](https://github.com/gorhill/uBlock/releases) mettendo il file xpi nella cartella del progetto (il nome del file deve essere uBlock.xpi).


## Utilizzo
_Il programma crea in automatico tutte le cartelle necessarie per il funzionamento._

Ci sono 2 modalita' di utilizzo:


### Single Scraping
Permette di scaricare tutti gli episodi di una singola serie.

```bash
python main.py -type 4 -e1 <link>
```


### Mass Scraping
Permette inanzittuto di scaricare tutti i dati di tutte le serie presenti sul sito e anche di scaricare tutti i video di tutti gli episodi delle serie.

**Per farlo basta seguire la seguente procedura**:

Passo 1:

Innanzitutto bisogna eseguire il file main.py con il parametro -type `1` in modo da poter generare un array con tutti i link delle serie:
```bash
python main.py -type 1
```

Passo 2:

Una volta generato l'array, bisogna eseguire il file main.py con il parametro -type `2` in modo da poter scaricare tutti i dati delle serie:
```bash
python main.py -type 2 -id 1 -e1 0 -e2 100
```

Parametri: 
- `-id` e' l'id del processo, se si vuole eseguire il programma piu' volte, bisogna cambiare questo parametro in modo che ogni computer abbia un id diverso.
- `-e1` e `-e2` sono il range delle serie di cui scaricare i dati, se si vuole scaricare tutte le serie, bisogna mettere `-e1 0 -e2 <numero delle serie>`.

Passo 3:

Una volta scaricati tutti i dati delle serie, bisogna eseguire il file main.py con il parametro -type `3` in modo da poter scaricare tutti i video di tutti gli episodi delle serie:
```bash
python main.py -type 3 -c true
```

Il parametro `-c` serve in caso venga messo in funzione anche se il programma non ha ancora finito il `passo 2`. In questo modo il programma attendera' che il `passo 2` avanzi.

## Esempi
```bash
python main.py -type 1
```

```bash
python main.py -type 2 -id 1 -e1 0 -e2 100
```

```bash
python main.py -type 3 -e1 true
```


## Contribuire
Le Pull Request sono benvenute. Per modifiche importanti, apri prima un problema per discutere cosa vorresti cambiare. 

## Licenza
Questo progetto è sotto licenza [MIT](https://choosealicense.com/licenses/mit/).