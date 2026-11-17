package workbench.modernjava.l04.demo;

/** Records are identity objects today. Here is what that identity looks like. */
public class IdentityDemo {

    // one physical copy of a book: its ISBN and its copy number
    record Copy(String isbn, int number) {}

    public static void main(String[] args) {
        Copy a = new Copy("9780441013593", 1);
        Copy b = new Copy("9780441013593", 1);

        System.out.println("equals: " + a.equals(b) + ", ==: " + (a == b));
        System.out.println("identity hash codes differ: " + (System.identityHashCode(a) != System.identityHashCode(b)));
        synchronized (a) {
            System.out.println("synchronized on a record: allowed, because it has an identity");
        }

        // the Integer box cache lets identity leak into == for some values and not others
        Integer x = 127, y = 127, p = 128, q = 128;
        System.out.println("Integer 127 == 127: " + (x == y) + ", 128 == 128: " + (p == q));

        // an array of records is an array of references to separate heap objects
        Copy[] shelf = { a, b, a };
        System.out.println("shelf[0] == shelf[2]: " + (shelf[0] == shelf[2]) + ", shelf[0] == shelf[1]: " + (shelf[0] == shelf[1]));
    }
}
