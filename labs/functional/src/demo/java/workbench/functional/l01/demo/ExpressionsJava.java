package workbench.functional.l01.demo;

import java.util.List;

/** Java twin of Expressions.kt. Java's if and try are statements; the switch expression (JDK 14) is the expression form. */
public class ExpressionsJava {

    enum AuthStatus { APPROVED, DECLINED, ERROR }

    // Statement style: declare a variable, then assign it in every branch.
    static AuthStatus statusStatement(int httpCode) {
        AuthStatus status;
        if (httpCode == 200) status = AuthStatus.APPROVED;
        else if (httpCode == 402) status = AuthStatus.DECLINED;
        else status = AuthStatus.ERROR;
        return status;
    }

    // Expression style: the switch expression IS the value.
    static AuthStatus statusOf(int httpCode) {
        return switch (httpCode) {
            case 200 -> AuthStatus.APPROVED;
            case 402 -> AuthStatus.DECLINED;
            default -> AuthStatus.ERROR;
        };
    }

    // Java's try is a statement, so the value has to leave through a return in each block.
    static long parseCents(String raw) {
        try {
            return Long.parseLong(raw);
        } catch (NumberFormatException e) {
            return -1;
        }
    }

    public static void main(String[] args) {
        for (int code : List.of(200, 402, 503)) {
            System.out.println(code + " -> " + statusOf(code) + " (statement version: " + statusStatement(code) + ")");
        }
        System.out.println("parseCents(\"1250\") = " + parseCents("1250"));
        System.out.println("parseCents(\"12x\")  = " + parseCents("12x"));
    }
}
