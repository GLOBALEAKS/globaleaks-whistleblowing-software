import {BehaviorSubject} from 'rxjs';
import {Inject, Injectable, Renderer2} from "@angular/core";
import {LangChangeEvent, TranslateService} from "@ngx-translate/core";
import {UtilsService} from "@app/shared/services/utils.service";
import {DOCUMENT} from "@angular/common";

@Injectable({
  providedIn: "root",
})
export class TranslationService {
  language = "";

  private currentLocale = new BehaviorSubject<string>("");
  currentLocale$ = this.currentLocale.asObservable();

  changeLocale(newLocale: string) {
    this.currentLocale.next(newLocale);
  }

  public currentDirection: string;

  constructor(private utilsService: UtilsService, protected translate: TranslateService, @Inject(DOCUMENT) private document: Document) {
    this.currentDirection = this.utilsService.getDirection(this.translate.currentLang);
  }

  onChange(changedLanguage: string, callback?: () => void) {
    this.language = changedLanguage;
    this.changeLocale(this.language);
    this.translate.use(this.language).subscribe(() => {
      if (callback) {
        callback();
      }
    });
  }
}
