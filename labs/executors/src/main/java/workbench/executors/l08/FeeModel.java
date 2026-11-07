package workbench.executors.l08;

/** Computes the processing fee for one ledger entry. Pure and cheap, so it's CPU work. */
public interface FeeModel {
    long feeCents(long amountCents);
}
