package workbench.bytecode.l02;

/** The Kotlin shapes from KotlinShapes.kt, called from Java: this is the API javap describes. */
public class KotlinShapesJava {
    public static void main(String[] args) {
        Scene duel = new Scene("The duel", 12);              // Java must pass every argument
        Scene ball = duel.copy("The ball", 20);              // copy() takes all of them too
        System.out.println(duel.getMinutes() + " " + duel.component1() + " " + ball);

        Actor ana = Actor.hire("ana");                       // @JvmStatic: a real static method
        Actor bo = Actor.Companion.guest("bo");              // no @JvmStatic: through the Companion
        ana.dressingRoom = "Room 4";                         // lateinit: a public field
        // ana.setLines(5);                                  // does not compile: private set, no setter
        System.out.println(ana.getLines() + " " + ana.isSpeaking() + " " + bo.getName());
        System.out.println("max=" + Actor.MAX_ROLES + " stage=" + Actor.Companion.getHOME_STAGE());

        Company.INSTANCE.getActors().add(ana);               // object: a singleton behind INSTANCE
        System.out.println(KotlinShapesKt.greet("Bo", '?'));  // top-level function: static on the file class
    }
}
