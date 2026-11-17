package workbench.functional.l01.demo;

import java.util.List;

/** Java twin of Expressions.kt. Java's if and try are statements; the switch expression (JDK 14) is the expression form. */
public class ExpressionsJava {

    // A recipe book marks each recipe with one, two or three stars.
    enum Difficulty { EASY, MEDIUM, HARD }

    // Statement style: declare a variable, then assign it in every branch.
    static Difficulty difficultyStatement(int stars) {
        Difficulty level;
        if (stars == 1) level = Difficulty.EASY;
        else if (stars == 2) level = Difficulty.MEDIUM;
        else level = Difficulty.HARD;
        return level;
    }

    // Expression style: the switch expression IS the value.
    static Difficulty difficultyOf(int stars) {
        return switch (stars) {
            case 1 -> Difficulty.EASY;
            case 2 -> Difficulty.MEDIUM;
            default -> Difficulty.HARD;
        };
    }

    // Java's try is a statement, so the value has to leave through a return in each block.
    static int parseGrams(String raw) {
        try {
            return Integer.parseInt(raw);
        } catch (NumberFormatException e) {
            return -1;
        }
    }

    public static void main(String[] args) {
        for (int stars : List.of(1, 2, 3)) {
            System.out.println(stars + " stars -> " + difficultyOf(stars) + " (statement version: " + difficultyStatement(stars) + ")");
        }
        System.out.println("parseGrams(\"250\") = " + parseGrams("250"));
        System.out.println("parseGrams(\"25O\") = " + parseGrams("25O"));      // typed with a letter O
    }
}
