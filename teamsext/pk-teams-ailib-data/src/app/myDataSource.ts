import { DataSource, Memory, RenderedPromptSection, Tokenizer } from "@microsoft/teams-ai";
import { TurnContext } from "botbuilder";
import * as path from "path";
import * as fs from "fs";

/**
 * A data source that searches through a local directory of files for a given query.
 */
export class MyDataSource implements DataSource {
    /**
     * Name of the data source.
     */
    public readonly name: string;

    /**
     * Local data.
     */
    private _data: { content: string; citation: string; }[];

    /**
     * Creates a new instance of the MyDataSource instance.
     */
    public constructor(name: string) {
        this.name = name;
    }

    /**
     * Initializes the data source.
     */
    public init() {
        const filePath = path.join(__dirname, "../data");
        const files = fs.readdirSync(filePath);
        this._data = files.map(file => {
            const data = 
            {
                content:fs.readFileSync(path.join(filePath, file), "utf-8"),
                citation:file
            };
            return data;
        });
    }

   
    public async renderData(context: TurnContext, memory: Memory, tokenizer: Tokenizer, maxTokens: number): Promise<RenderedPromptSection<string>> {
        const query = memory.getValue("temp.input") as string;
        if(!query) {
            return { output: "", length: 0, tooLong: false };
        }
        for (let data of this._data) {
            if (data.content.includes(query)) {
                return { output: this.formatDocument(`${data.content}\n Citation title:${data.citation}`), length: data.content.length, tooLong: false };
            }
        }
        if (query.toLocaleLowerCase().includes("perksplus")) {
            return { output: this.formatDocument(`${this._data[0].content}\n Citation title:${this._data[0].citation}`), length: this._data[0].content.length, tooLong: false };
        } else if (query.toLocaleLowerCase().includes("company") || query.toLocaleLowerCase().includes("history")) {
            return { output: this.formatDocument(`${this._data[1].content}\n Citation title:${this._data[1].citation}`), length: this._data[1].content.length, tooLong: false };
        } else if (query.toLocaleLowerCase().includes("northwind") || query.toLocaleLowerCase().includes("health")) {
            return { output: this.formatDocument(`${this._data[2].content}\n Citation title:${this._data[2].citation}`), length: this._data[2].content.length, tooLong: false };
        }
        return { output: "", length: 0, tooLong: false };
    }

    /**
     * Formats the result string 
     * @param result 
     * @returns 
     */
    private formatDocument(result: string): string {
        return `<context>${result}</context>`;
    }
}