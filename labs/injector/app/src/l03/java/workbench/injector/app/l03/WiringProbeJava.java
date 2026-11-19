package workbench.injector.app.l03;

/**
 * The Java twin of WiringProbe: Java calling the same generated component, or the same reflection container,
 * in a fresh JVM started by StartupRaceJava. Prints how long each step took, in microseconds.
 */
public class WiringProbeJava {
    public static void main(String[] args) {
        String way = args.length > 0 ? args[0] : "generated";
        long t0 = System.nanoTime();
        MovingDay day;
        long t1, t2;
        if (way.equals("generated")) {
            MovingDayComponent plan = new GeneratedMovingDayComponent();
            t1 = System.nanoTime();
            day = plan.movingDay();
            t2 = System.nanoTime();
            plan.movingDay();
        } else {
            ReflectionContainer container = new ReflectionContainer(RouteModule.INSTANCE);
            t1 = System.nanoTime();
            day = container.get(MovingDay.class);
            t2 = System.nanoTime();
            container.get(MovingDay.class);
        }
        long t3 = System.nanoTime();
        System.out.println("probe " + way + " create=" + (t1 - t0) / 1000 + " first=" + (t2 - t1) / 1000
                + " second=" + (t3 - t2) / 1000 + " " + day.plan().get(0));
    }
}
