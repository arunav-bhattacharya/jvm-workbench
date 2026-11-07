package workbench.generics.l09.demo;

/** Java twin of ClassApiDemo.kt: the same checks and names, on java.lang.Class. */
public class ClassApiDemoJava {
    public static void main(String[] args) {
        PaymentEvent event = new CardAuthorized("pay_1", 1_200);

        Class<CardAuthorized> c = CardAuthorized.class;
        System.out.println("c.getSimpleName() = " + c.getSimpleName() + ", event.getClass() == c: " + (event.getClass() == c));

        System.out.println("isInstance: " + c.isInstance(event) + ", cast(...).getCents(): " + c.cast(event).getCents()
            + ", no safeCast in Java: " + (RefundIssued.class.isInstance(event) ? RefundIssued.class.cast(event) : null));
        try {
            RefundIssued.class.cast(event);
        } catch (ClassCastException e) {
            System.out.println("cast failed: " + e.getMessage());
        }

        System.out.println("getSimpleName = " + c.getSimpleName() + ", getName = " + c.getName());
        System.out.println("int.class = " + int.class + ", Integer.class = " + Integer.class);
    }
}
