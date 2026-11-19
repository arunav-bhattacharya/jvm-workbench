package workbench.ksp.app.l03;

// The Java twin: Java reading the labels that KSP generated in Kotlin. A `const val` in an object compiles to a
// public static final field, so Java reads LampLabel.SHAPE directly.
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l03.MoveMateJava -Pmine=l03
public class MoveMateJava {
    public static void main(String[] args) {
        System.out.println(LampLabel.SHAPE);
        System.out.println(BookshelfLabel.SHAPE + " -> " + BookshelfLabel.ROOM + ", " + BookshelfLabel.HANDLING);
        System.out.println(PlantLabel.SHAPE + " -> " + PlantLabel.ROOM + ", " + PlantLabel.HANDLING);
        System.out.println(MirrorLabel.SHAPE + " -> " + MirrorLabel.ROOM);
        System.out.println(MovingCrateLabel.SHAPE);
    }
}
