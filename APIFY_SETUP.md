# Vinted-FindFications: provider Apify (opzionale)

L'endpoint non ufficiale `/api/v2/catalog/items` non funziona più. Il container
Vinted-FindFications riceve inoltre un challenge Cloudflare anche da `/catalog`.
Per questo la ricerca manuale usa, **solo se configurato**, un provider esterno
a pagamento: [amitaviv/vinted-scraper](https://apify.com/amitaviv/vinted-scraper).

## Attivazione nello stack già presente

1. Registra un account Apify; prova prima l'Actor manualmente dalla Console
   con la stessa ricerca Vinted e controlla **Output** e **Costi**.
2. Copia il token API da Apify Console > Settings > Integrations.
3. In Portainer > Stacks > vinted-notifications > Editor usa
   `docker-compose.findfications.yml` mantenendo lo stesso nome di stack e volumi.
4. Nella sezione delle variabili dello stack inserisci `APIFY_TOKEN` (non
   committarlo nel repository). Mantieni `APIFY_AUTO_ENABLED=false`.
5. Update stack, pull nuova immagine `ghcr.io/giuliorizzolio/vinted-findfications:catalogo`.
6. Apri http://192.168.1.110:8001/catalogo e prova una ricerca breve.

Le ricerche del Catalogo partono soltanto quando premi **Cerca**.
Puoi filtrare il titolo e, con **Carica anche le descrizioni**, testo delle
descrizioni (costo aggiuntivo e ricerca più lenta). Se la descrizione non è
disponibile, non viene inventata.

## Monitoraggio automatico: attivazione separata

Imposta `APIFY_AUTO_ENABLED=true` **solo dopo** aver verificato costi e ricerca
manuale. Il polling usa le ricerche già presenti nel database; intervallo
minimo 30 minuti, anche se la Web UI mostra 60 secondi. Le prime inserzioni
raccolte diventano la baseline locale, senza inviare avvisi per vecchi annunci.
Gli inserimenti successivi vengono inoltrati al sistema Notifications.

Il provider usa memoria `onlyNew` anche sul proprio account Apify, quindi
la deduplica non riguarda soltanto la scansione corrente.

**Costi**: Apify addebita un prezzo a esecuzione e per annuncio restituito,
oltre all'eventuale dettaglio articolo. I costi precisi dipendono dal piano.
Non abilitare il monitor senza aver fissato un budget sulla piattaforma.

**Limiti**: il provider è di terze parti, non un'API ufficiale Vinted;
può riscontrare blocchi o cambi di layout. La build Docker e i test con mock
non verificano l'accesso reale al catalogo del tuo account.
Anche gli annunci che ricompaiono in ordine recente possono essere segnalati
come nuovi. Nessuna promessa di notifiche in tempo reale.

**Sicurezza**: non condividere il token Apify nei log o negli screenshot.
Non inserire password Vinted in questo progetto.
