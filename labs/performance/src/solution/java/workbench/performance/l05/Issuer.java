package workbench.performance.l05;

/** The card issuer's API: approves or declines one payment. Real ones take 100 ms or more. */
@FunctionalInterface
public interface Issuer {
    boolean approve(String merchant, long amountCents);
}
