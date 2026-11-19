package workbench.ksp.app.l08;

import java.util.List;

// The Java twin of Packing.kt: Java calling the builders and cards KSP generated in Kotlin. A builder is an
// ordinary class; a card is an extension function, so Java calls it as a static method that takes the Lamp.
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l08.PackingJava
public class PackingJava {
    public static void main(String[] args) {
        Lamp lamp = new LampBuilder().name("desk lamp").bulbs(1).shade(null).build();
        Bookshelf shelf = new BookshelfBuilder().shelves(3).books(List.of("Dune", "Emma")).build();
        System.out.println(LampInventoryCardKt.inventoryCard(lamp));
        System.out.println(BookshelfInventoryCardKt.inventoryCard(shelf));
    }
}
