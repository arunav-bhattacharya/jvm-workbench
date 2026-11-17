package workbench.startup.l02.fixtures;

final class Status {
    private Status() {
    }

    static String format(int stopsLeft) {
        return stopsLeft == 0 ? "delivered" : "out for delivery, " + stopsLeft + (stopsLeft == 1 ? " stop" : " stops") + " to go";
    }
}
