package workbench.kotlin.l04.demo;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Java twin of BuildersDemo.kt. Java builds a mutable collection, then copies it into an
 * unmodifiable one. buildList and buildString are inline-only Kotlin functions, so Java can't call them.
 */
public class BuildersDemoJava {

    record LineJava(String file, int copies, int pages) {}

    public static void main(String[] args) {
        List<LineJava> building = new ArrayList<>();
        building.add(new LineJava("flyer.pdf", 250, 1));
        building.add(new LineJava("menu.pdf", 40, 8));
        if (building.size() == 2) building.add(new LineJava("cover-sheet.pdf", 1, 1));
        List<LineJava> lines = List.copyOf(building);

        Map<String, Integer> printed = new LinkedHashMap<>();
        for (LineJava l : lines) printed.put(l.file(), l.copies() * l.pages());

        String text = new StringBuilder()
                .append("pages to print=")
                .append(printed.values().stream().mapToInt(Integer::intValue).sum())
                .toString();

        System.out.println(lines.stream().map(LineJava::file).toList());
        System.out.println(printed);
        System.out.println(text);
        try {
            lines.add(new LineJava("late.pdf", 1, 1));
        } catch (UnsupportedOperationException e) {
            System.out.println("the copied list is read-only: " + e.getClass().getSimpleName());
        }
    }
}
