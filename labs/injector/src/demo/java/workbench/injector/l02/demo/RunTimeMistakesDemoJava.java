package workbench.injector.l02.demo;

import java.util.concurrent.Callable;

// Java asking the same Kotlin reflection container for the same three broken plans.
//   ./gradlew :injector:demo -Pmain=workbench.injector.l02.demo.RunTimeMistakesDemoJava
public class RunTimeMistakesDemoJava {
    public static void main(String[] args) {
        tryOnTheDay("missing: Driver has no @Inject",
                () -> new ReflectionContainer().get(workbench.injector.l02.demo.missing.MovingDay.class));
        tryOnTheDay("cycle: the driver waits for the truck",
                () -> new ReflectionContainer().get(workbench.injector.l02.demo.cycle.MovingDay.class));
        tryOnTheDay("twice: two routes, no names", () -> {
            var day = new ReflectionContainer(workbench.injector.l02.demo.twice.RouteModule.INSTANCE)
                    .get(workbench.injector.l02.demo.twice.MovingDay.class);
            return "the driver takes the " + day.getCrew().getTruck().getDriver().getRoute().getName();
        });
    }

    private static void tryOnTheDay(String title, Callable<Object> morning) {
        System.out.println("--- " + title);
        try {
            System.out.println("no error: " + morning.call());
        } catch (Throwable e) {
            System.out.println(e);
            System.out.println("  " + e.getStackTrace().length + " stack frames, the first three:");
            for (int i = 0; i < 3 && i < e.getStackTrace().length; i++) System.out.println("    at " + e.getStackTrace()[i]);
        }
    }
}
