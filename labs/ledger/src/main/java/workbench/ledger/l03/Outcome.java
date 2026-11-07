package workbench.ledger.l03;

/** What the ledger did with a transfer. */
public enum Outcome {
    /** The money moved: the debit and the credit both happened. */
    APPLIED,
    /** Nothing moved: the source account did not hold enough money. */
    INSUFFICIENT_FUNDS
}
