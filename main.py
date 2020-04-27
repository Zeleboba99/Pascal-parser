import os
from grammar import *


def main():
    prog2='''
    Program t;
    var
    g : integer;
    procedure t;
    var 
    d: integer;
    begin 
    a:=78;   
    end;
    BEGIN
    a:=1;
    b[1]:=0;
    b[1]:=a[0];
    END.
    '''
    prog1 = '''
        Program t;
        var                    
            k, d: integer;
            j: char;
            g, c: array [1 .. 100] of integer;
        function t(j:integer; k: char):integer;
        var 
            d: integer;
        begin 
        a:= 0;   
        end;
        procedure t;
        var 
            d: integer;
        begin 
        a:=78;   
        end;
            g: integer;
        BEGIN
        g[0]:=10;
        g[1]:=c[0];
        writeln(a, 3, "df", 7+9);
        for ( i:=2 to 10  ) do
        begin
            k:=2 mod 3;
            l:=j div 4;
            l:=i+8;
            k:=0;
        end;
        while (i>3) do        
            a:=k+2;                    
        for (i:=2 to 6 ) do 
            g:=0;
            s:=0;
        if (k>2 and j>=2) then
            begin        
            f:=9;
            end;
        else 
            v:=3;         
        END.            
    '''

    g = PascalGrammar()
    prog1 = g.parse(prog1)
    print(*prog1.tree, sep=os.linesep)


if __name__ == "__main__":
    main()
