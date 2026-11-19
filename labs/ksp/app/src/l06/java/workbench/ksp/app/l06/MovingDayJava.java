package workbench.ksp.app.l06;

// Lesson 6, Try it: the same calls from Java. A top-level Kotlin function lives in a class named after its file,
// so the extension Lamp.receipt(...) from LampReceipt.kt is the static method LampReceiptKt.receipt(lamp, ...).
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l06.MovingDayJava
public class MovingDayJava {
    public static void main(String[] args) {
        LampReceipt lampReceipt = LampReceiptKt.receipt(new Lamp("desk lamp", 1, null), "Ana");
        VanReceipt vanReceipt = VanReceiptKt.receipt(new Van("MV-1", lampReceipt), "Ben");

        System.out.println(BoxInventoryCardKt.inventoryCard(new Box("plates", "kitchen", 4200, true)));
        System.out.println(LampReceiptInventoryCardKt.inventoryCard(lampReceipt));
        System.out.println(VanReceiptInventoryCardKt.inventoryCard(vanReceipt));
    }
}
