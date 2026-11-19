package workbench.ksp.app.l04;

import workbench.ksp.app.l04.van.Load;
import workbench.ksp.app.l04.van.LoadBuilder;

import java.util.Arrays;

// Lesson 4, Try it: Java calling the same builders. KSP generated Kotlin, which compiles to ordinary classes.
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l04.MoveDayJava
public class MoveDayJava {
    public static void main(String[] args) {
        Lamp lamp = new LampBuilder().name("desk lamp").bulbs(1).shade(null).build();
        Box plates = new BoxBuilder().label("plates").room("kitchen").weightGrams(4200).fragile(true).build();
        Load load = new LoadBuilder().first(plates).spares(Arrays.asList(null, plates)).build();
        Kitchen.Drawer drawer = new KitchenDrawerBuilder().label("spoons").handles(2).build();
        Crate crate = new CrateBuilder().in("hall").object("mirror").build();   // in and object are fine names in Java

        System.out.println(lamp);
        System.out.println(plates);
        System.out.println("load: first=" + load.getFirst().getLabel() + ", spares=" + load.getSpares().size());
        System.out.println(drawer);
        System.out.println("crate: in=" + crate.getIn() + ", object=" + crate.getObject());
        try {
            new PlantBuilder().kind("fern").potLitres(2.5).build();
        } catch (IllegalStateException e) {
            System.out.println(e.getMessage());
        }
    }
}
