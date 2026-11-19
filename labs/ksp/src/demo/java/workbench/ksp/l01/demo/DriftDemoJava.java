package workbench.ksp.l01.demo;

// The Java twin of DriftDemo.kt: a record gained a component, watts, and the hand-written card didn't.
//   ./gradlew :ksp:demo -Pmain=workbench.ksp.l01.demo.DriftDemoJava
public class DriftDemoJava {

    record Lamp(String name, int bulbs, String shade, int watts) {}

    // the card, exactly as it was written for the old Lamp
    static String inventoryCard(Lamp lamp) {
        return "Lamp: name=" + lamp.name() + ", bulbs=" + lamp.bulbs() + ", shade=" + lamp.shade();
    }

    public static void main(String[] args) {
        Lamp lamp = new Lamp("desk lamp", 1, null, 40);
        System.out.println("the lamp: " + lamp);
        System.out.println("its card: " + inventoryCard(lamp));
    }
}
