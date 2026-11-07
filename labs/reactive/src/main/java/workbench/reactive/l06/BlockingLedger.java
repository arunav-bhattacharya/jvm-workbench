package workbench.reactive.l06;

import java.math.BigDecimal;

/** A JDBC-style ledger repository: every call blocks the calling thread until the database answers. */
public interface BlockingLedger {
    BigDecimal balance(String account);
}
