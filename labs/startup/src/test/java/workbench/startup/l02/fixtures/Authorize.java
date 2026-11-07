package workbench.startup.l02.fixtures;

final class Authorize {
    private Authorize() {
    }

    static String run(String request) {
        return "AUTHORIZED " + Money.format(1250);
    }
}
