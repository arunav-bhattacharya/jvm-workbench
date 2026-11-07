package workbench.startup.l02.fixtures;

final class Refund {
    private Refund() {
    }

    static String run(String request) {
        return "REFUNDED " + Money.format(990);
    }
}
