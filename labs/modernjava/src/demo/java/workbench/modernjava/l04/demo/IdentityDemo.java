package workbench.modernjava.l04.demo;

/** Records are identity objects today. Here is what that identity looks like. */
public class IdentityDemo {

    record Money(long minor, String currency) {}

    public static void main(String[] args) {
        Money a = new Money(4_200, "EUR");
        Money b = new Money(4_200, "EUR");

        System.out.println("equals: " + a.equals(b) + ", ==: " + (a == b));
        System.out.println("identity hash codes differ: " + (System.identityHashCode(a) != System.identityHashCode(b)));
        synchronized (a) {
            System.out.println("synchronized on a record: allowed, because it has an identity");
        }

        // the Integer box cache lets identity leak into == for some values and not others
        Integer x = 127, y = 127, p = 128, q = 128;
        System.out.println("Integer 127 == 127: " + (x == y) + ", 128 == 128: " + (p == q));

        // an array of records is an array of references to separate heap objects
        Money[] ledger = { a, b, a };
        System.out.println("ledger[0] == ledger[2]: " + (ledger[0] == ledger[2]) + ", ledger[0] == ledger[1]: " + (ledger[0] == ledger[1]));
    }
}
