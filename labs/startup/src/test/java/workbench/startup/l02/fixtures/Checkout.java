package workbench.startup.l02.fixtures;

/** The "application" a training run drives. Each kind of request touches different classes. */
public final class Checkout {
    private Checkout() {
    }

    public static String handle(String request) {
        if (request.startsWith("authorize")) {
            return Authorize.run(request);
        }
        if (request.startsWith("refund")) {
            return Refund.run(request);
        }
        return "unknown request";
    }
}
