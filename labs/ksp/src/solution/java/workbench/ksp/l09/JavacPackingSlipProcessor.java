package workbench.ksp.l09;

import java.io.IOException;
import java.io.Writer;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Set;
import javax.annotation.processing.AbstractProcessor;
import javax.annotation.processing.Messager;
import javax.annotation.processing.RoundEnvironment;
import javax.annotation.processing.SupportedAnnotationTypes;
import javax.annotation.processing.SupportedOptions;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.Element;
import javax.lang.model.element.ElementKind;
import javax.lang.model.element.Modifier;
import javax.lang.model.element.TypeElement;
import javax.lang.model.element.VariableElement;
import javax.lang.model.util.ElementFilter;
import javax.tools.Diagnostic;
import javax.tools.StandardLocation;
import workbench.ksp.annotations.Inventory;
import workbench.ksp.annotations.Room;

/**
 * Lesson 9, given and read-only: the Java team's packing slip processor, a javac annotation processor
 * (javax.annotation.processing, part of the JDK since Java 6). For every class annotated @Inventory it writes one
 * line into META-INF/movemate/packing-slip.txt: the class name, its room from @Room, and its fields in order.
 * Your job in PackingSlipProcessor.kt is to port it to KSP, move by move, so Kotlin classes get the same slip.
 *
 * In a Java build it would run through Gradle's annotationProcessor configuration, registered in
 * META-INF/services/javax.annotation.processing.Processor, and declared aggregating for Gradle's incremental
 * compile in META-INF/gradle/incremental.annotation.processors:
 *     workbench.ksp.l09.JavacPackingSlipProcessor,aggregating
 */
@SupportedAnnotationTypes("workbench.ksp.annotations.Inventory")
@SupportedOptions("movemate.household")
public class JavacPackingSlipProcessor extends AbstractProcessor {

    private boolean slipWritten = false;

    @Override
    public SourceVersion getSupportedSourceVersion() {
        return SourceVersion.latestSupported();
    }

    @Override
    public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment roundEnv) {
        if (slipWritten || roundEnv.processingOver()) return false;
        Messager messager = processingEnv.getMessager();
        String household = processingEnv.getOptions().getOrDefault("movemate.household", "MoveMate");

        // 1. Find: every element annotated @Inventory in this round
        List<TypeElement> classes = new ArrayList<>();
        for (Element element : roundEnv.getElementsAnnotatedWith(Inventory.class)) {
            // 2. Check: only classes, with an error on the exact element
            if (element.getKind() != ElementKind.CLASS) {
                messager.printMessage(Diagnostic.Kind.ERROR,
                        "@Inventory goes on a class, but " + element.getSimpleName() + " is " + kindWords(element.getKind()),
                        element);
                continue;
            }
            classes.add((TypeElement) element);
        }
        if (classes.isEmpty()) return false;
        classes.sort(Comparator.comparing(c -> c.getSimpleName().toString()));

        // 3. Read: one line per class, its fields in source order
        List<String> lines = new ArrayList<>();
        for (TypeElement type : classes) lines.add(slipLine(type));

        // 4. Write: one resource for all of them; the originating elements tell an incremental build where it came from
        try {
            var slip = processingEnv.getFiler().createResource(StandardLocation.CLASS_OUTPUT, "",
                    "META-INF/movemate/packing-slip.txt", classes.toArray(new Element[0]));
            try (Writer out = slip.openWriter()) {
                out.write("# " + household + " packing slip. Generated, do not edit.\n");
                for (String line : lines) out.write(line + "\n");
            }
        } catch (IOException e) {
            messager.printMessage(Diagnostic.Kind.ERROR, "could not write the packing slip: " + e.getMessage());
        }
        slipWritten = true;
        return false; // don't claim @Inventory: other processors may want it too
    }

    /** "Lamp [living room]: name, bulbs, shade" */
    static String slipLine(TypeElement type) {
        Room room = type.getAnnotation(Room.class);
        List<String> names = new ArrayList<>();
        for (VariableElement field : ElementFilter.fieldsIn(type.getEnclosedElements())) {
            if (!field.getModifiers().contains(Modifier.STATIC)) names.add(field.getSimpleName().toString());
        }
        return type.getSimpleName() + " [" + (room == null ? "no room" : room.name()) + "]: " + String.join(", ", names);
    }

    /** The same words the KSP port uses for each kind of declaration. */
    static String kindWords(ElementKind kind) {
        return switch (kind) {
            case INTERFACE -> "an interface";
            case ENUM -> "an enum";
            case ANNOTATION_TYPE -> "an annotation";
            case RECORD -> "a record";
            default -> "a " + kind.name().toLowerCase();
        };
    }
}
