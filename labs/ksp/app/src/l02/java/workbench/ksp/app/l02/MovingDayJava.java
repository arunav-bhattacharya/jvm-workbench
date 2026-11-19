package workbench.ksp.app.l02;

import java.util.List;

// The Java twin: Java calling the cards your processor generated. LampInventoryCard.kt compiles to the class
// LampInventoryCardKt, and the extension function becomes a static method that takes the lamp.
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l02.MovingDayJava -Pmine=l02
public class MovingDayJava {
    public static void main(String[] args) {
        List<String> van = List.of(
                BoxInventoryCardKt.inventoryCard(new Box("kitchen 1", "kitchen", 5200, true)),
                LampInventoryCardKt.inventoryCard(new Lamp("desk lamp", 1, null)),
                BookshelfInventoryCardKt.inventoryCard(new Bookshelf(3, List.of("atlas", "cookbook"))),
                PlantInventoryCardKt.inventoryCard(new Plant("fern", 2.5, 7)));
        van.forEach(System.out::println);
    }
}
