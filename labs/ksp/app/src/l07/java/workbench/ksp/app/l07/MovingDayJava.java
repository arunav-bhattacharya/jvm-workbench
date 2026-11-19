package workbench.ksp.app.l07;

import java.util.List;

// The Java twin of MovingDay.kt: Java calling the master list KSP generated in Kotlin. MovingDayList is a Kotlin
// object, so Java reaches it through its INSTANCE field; the names property is the getter getNames().
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l07.MovingDayJava
public class MovingDayJava {
    public static void main(String[] args) {
        List<Object> things = List.of(
                new Box("books", "study", 12_000, false),
                new Lamp("desk lamp", 1, null),
                new Bookshelf(3, List.of("Dune", "Emma")),
                new Plant("fern", 2.5, 7));
        System.out.println("MovingDayList: " + MovingDayList.INSTANCE.getNames());
        for (Object thing : things) System.out.println(MovingDayList.INSTANCE.cardFor(thing));
    }
}
