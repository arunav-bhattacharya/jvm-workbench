package workbench.executors.l08;

/** Computes the card fee on one payment. Pure and cheap, so it's CPU work. */
public interface FeeModel {
    long feeCents(long amountCents);
}
