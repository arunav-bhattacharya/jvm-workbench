package workbench.injector.app.l02;

// Java calling the same generated Kotlin component.
//   ./gradlew :injector:app:demo -Pmain=workbench.injector.app.l02.MovingDayAppJava
public class MovingDayAppJava {
    public static void main(String[] args) {
        MovingDayComponent plan = new GeneratedMovingDayComponent();
        plan.movingDay().plan().forEach(System.out::println);
        System.out.println("one truck for the whole day: " + (plan.truck() == plan.movingDay().getCrew().getTruck()));
    }
}
