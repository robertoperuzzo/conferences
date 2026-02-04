# Smart Chunks, Better Search

## Perché il chatbot non ha trovato la risposta quando il documento la conteneva chiaramente?

## Panoramica

### Introduzione Coinvolgente

Ottenere risposte di qualità da un chatbot o da un sistema di ricerca semantica non riguarda solo il modello, dipende anche da quanto bene sono preparati i dati. Il _chunking_ gioca un ruolo fondamentale nell'efficacia della Retrieval-Augmented Generation (RAG). In questa sessione, sposteremo l’attenzione dai casi d’uso appariscenti al lavoro dietro le quinte che li rende possibili.

Esploreremo le strategie di chunking disponibili oggi, come influenzano la qualità del recupero e quali strumenti possono aiutarti a farlo correttamente—dai _chunker_ leggeri e sensibili alla sintassi ai parser semantici basati su AI.

### Prerequisiti

Conoscenza di base della ricerca vettoriale e interesse per i workflow potenziati dall’AI. Non è richiesta una conoscenza approfondita di AI o data science; solo la voglia di andare oltre le basi.

### Struttura della Sessione

In questa sessione esploreremo perché **il chunking è un elemento critico della pipeline RAG (Retrieval-Augmented Generation)** e come il modo in cui suddividiamo i contenuti può determinare la qualità delle risposte AI. Spesso, quando le risposte non sono soddisfacenti, il problema non è il LLM stesso, ma come i documenti sono stati preparati.

Come parte di un **investigazione pratica**, abbiamo esplorato quali strumenti e strategie aiutano a rendere il chunking efficace. Per estrarre e preparare testo dai PDF, abbiamo sperimentato:

- **PyPDFParser**
- **MarkItDown**
- **Unstructured.io**
- **Marker**

Successivamente, analizzeremo diverse **strategie di chunking** e vedremo come ciascuna influenzi la qualità del recupero:

- **Dimensione fissa**
- **Semantico**, usando `SemanticChunker` di LangChain
- **Sliding window**, utilizzando `RecursiveCharacterTextSplitter` di LangChain per creare chunk sovrapposti con consapevolezza della struttura del documento

Attraverso questa esplorazione pratica, discuteremo anche dei **compromessi tra qualità e prestazioni**, condivideremo alcune metriche di base e evidenzieremo le principali lezioni apprese.

### Obiettivi di Apprendimento

- Comprendere come il chunking influenzi la qualità delle risposte nei sistemi di ricerca vettoriale e RAG
- Scoprire strumenti e librerie moderne che migliorano la segmentazione e il preprocessing dei documenti
- Valutare i compromessi e scegliere l’approccio migliore in base alle esigenze del progetto
