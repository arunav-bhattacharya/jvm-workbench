package workbench.startup.l02.fixtures;

final class Redirect {
    private Redirect() {
    }

    static String run(String request) {
        return "PX-1042 REDIRECTED, " + Status.format(1);
    }
}
