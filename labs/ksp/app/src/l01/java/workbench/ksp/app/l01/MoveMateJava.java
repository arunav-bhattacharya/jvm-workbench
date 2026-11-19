package workbench.ksp.app.l01;

import java.util.List;

// The Java twin: Java calling the cards that KSP generated in Kotlin. Each generated file compiles to an
// ordinary class (LampInventoryCard.kt becomes LampInventoryCardKt) with a static method that takes the object.
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l01.MoveMateJava
public class MoveMateJava {
    public static void main(String[] args) {
        System.out.println(BoxInventoryCardKt.inventoryCard(new Box("kitchen 1", "kitchen", 5200, true)));
        System.out.println(LampInventoryCardKt.inventoryCard(new Lamp("desk lamp", 1, null)));
        System.out.println(BookshelfInventoryCardKt.inventoryCard(new Bookshelf(3, List.of("atlas", "cookbook"))));
        System.out.println(PlantInventoryCardKt.inventoryCard(new Plant("fern", 2.5, 7))); // Java passes the default
    }
}
