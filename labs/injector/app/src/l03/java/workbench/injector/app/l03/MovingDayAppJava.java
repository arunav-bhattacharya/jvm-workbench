package workbench.injector.app.l03;

// Java calling the same generated component: the GPS stays off until the truck first asks for directions.
//   ./gradlew :injector:app:demo -Pmain=workbench.injector.app.l03.MovingDayAppJava
public class MovingDayAppJava {
    public static void main(String[] args) {
        long start = System.nanoTime();
        MovingDayComponent plan = new GeneratedMovingDayComponent();
        MovingDay day = plan.movingDay();
        System.out.println("crew ready after " + ms(start) + " ms, GPS switched on: " + GpsUnit.Companion.getSwitchedOn());
        day.plan().forEach(System.out::println);
        System.out.println(plan.truck().directions());
        System.out.println("first directions after " + ms(start) + " ms, GPS switched on: " + GpsUnit.Companion.getSwitchedOn());
        System.out.println(plan.truck().directions());
        System.out.println("second directions after " + ms(start) + " ms, GPS switched on: " + GpsUnit.Companion.getSwitchedOn());
    }

    private static long ms(long start) {
        return (System.nanoTime() - start) / 1_000_000;
    }
}
