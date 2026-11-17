package workbench.performance.l05;

public final class Librarian {
    private final DocumentStore store;

    public Librarian(DocumentStore store) {
        this.store = store;
    }

    public String lookup(String shelf, String title) {
        LookupEvent event = new LookupEvent();
        event.begin();                                   // 1. start the clock
        String text = store.fetch(shelf, title);
        event.end();                                     // 2. stop it: the duration is the store call
        if (event.shouldCommit()) {                      // 3. false when no recording wants this event
            event.shelf = shelf;
            event.title = title;
            event.found = text != null;
            event.commit();                              // 4. write it into the recording's buffers
        }
        return text;
    }
}
