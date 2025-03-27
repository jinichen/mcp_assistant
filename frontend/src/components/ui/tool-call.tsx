"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Code, Check } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

interface ToolCallProps {
  toolCall: {
    id: string;
    type: string;
    function: {
      name: string;
      arguments: string;
    };
  };
  result?: any;
  isLoading?: boolean;
}

export function ToolCall({ toolCall, result, isLoading }: ToolCallProps) {
  // Format JSON parameters
  const formatArguments = (argsStr: string) => {
    try {
      const args = JSON.parse(argsStr);
      return JSON.stringify(args, null, 2);
    } catch (e) {
      return argsStr;
    }
  };

  return (
    <div className="space-y-2 my-4">
      {/* Tool call card */}
      <Card className="border-l-4 border-l-primary">
        <CardHeader className="py-2">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Code size={16} className="text-primary" />
            Tool Call: <Badge variant="outline">{toolCall.function.name}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="py-2">
          <div className="text-xs text-muted-foreground mb-1">Parameters:</div>
          <pre className="bg-muted p-2 rounded-md text-xs overflow-auto max-h-[200px]">
            {formatArguments(toolCall.function.arguments)}
          </pre>
        </CardContent>
      </Card>
      
      {/* Loading state or result */}
      {isLoading ? (
        <div className="flex justify-center my-2">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
        </div>
      ) : result && (
        <Card className="border-l-4 border-l-green-500">
          <CardHeader className="py-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Check size={16} className="text-green-500" />
              Tool Result
            </CardTitle>
          </CardHeader>
          <CardContent className="py-2">
            <pre className="bg-muted p-2 rounded-md text-xs overflow-auto max-h-[200px]">
              {typeof result === 'object' ? JSON.stringify(result, null, 2) : result}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}