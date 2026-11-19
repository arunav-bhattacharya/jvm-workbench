package workbench.ksp.app.l05;

// Lesson 5, Try it: the same builders from Java.
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l05.ChecksJava
public class ChecksJava {
    public static void main(String[] args) {
        Plant fern = new PlantBuilder().kind("fern").potLitres(2.5).waterEveryDays(3).build();
        Box plates = new BoxBuilder().label("plates").room("kitchen").weightGrams(4200).fragile(true).build();
        System.out.println(fern);
        System.out.println(plates);
    }
}
