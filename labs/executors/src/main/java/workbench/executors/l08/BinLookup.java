package workbench.executors.l08;

/** Looks up the issuing bank for a card BIN. Blocking: it calls a remote service. */
public interface BinLookup {
    String issuer(String bin);
}
