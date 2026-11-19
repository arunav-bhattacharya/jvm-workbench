package workbench.injector.app.l01;

// Java calling the same generated Kotlin component: once compiled, it is an ordinary class.
//   ./gradlew :injector:app:demo -Pmain=workbench.injector.app.l01.MovingDayAppJava
public class MovingDayAppJava {
    public static void main(String[] args) {
        MovingDayComponent plan = new GeneratedMovingDayComponent();
        MovingDay day = plan.movingDay();
        day.plan().forEach(System.out::println);
        System.out.println("one truck for the whole day: " + (plan.truck() == day.getCrew().getTruck()));
        System.out.println("tape rolls made: " + TapeRoll.Companion.getMade());
    }
}
