package workbench.jmm.l05;

/** A connection to one card issuer, the bank that issued a card. Expensive to create. (Given; not part of the exercise.) */
public record IssuerClient(String issuerId, long connectionNumber) {}
