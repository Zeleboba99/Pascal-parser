import os
import mel_parser


def main():
    prog1 = '''
        Program t;
        var                    
            k, d: integer;
            j: char;
            g, c: array [1 .. 100] of integer;
        function t(j:integer; k: char);
        var 
            d: integer;
        begin 
        a:= 0;   
        end;
        procedure t(j:integer; k: char);
        var 
            d: integer;
        begin 
        a:=78;   
        end;
            g: integer;
        BEGIN
        writeln(a, 3, "df", 7+9);
        repeat 
         k:=2 mod 3;
            l:=j div 4;
            l:=i+8;
            k:=0;
        until (l<2)
        while (i>3) do        
            a:=k+2;                    
        for (i:=2 to 0 ) do 
            g:=0;
            s:=0;
        if (k>2) then
            begin        
            f:=9;
            end;
        else 
            v:=3;         
        END.            
    '''

    prog1 = mel_parser.parse(prog1)
    print(*prog1.tree, sep=os.linesep)


if __name__ == "__main__":
    main()
