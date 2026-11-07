package workbench.executors.l09;

import java.util.List;

/** Fetches a merchant's ledger lines for the month. Blocking: it queries the database. */
public interface LedgerClient {
    List<String> lines(String merchantId);
}
