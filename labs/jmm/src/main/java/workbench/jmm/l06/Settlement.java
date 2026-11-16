package workbench.jmm.l06;

/** A payment record that one thread fills in and hands to another. Given; not part of the exercise. Its fields are plain and mutable on purpose. */
public final class Settlement {
    public long id;
    public long amountCents;
    public String currency;
}
